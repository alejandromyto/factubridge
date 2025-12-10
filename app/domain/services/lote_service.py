"""
app/domain/services/lote_service.py

Servicio de dominio para gestión de lotes de envío.

Responsabilidades:
- Validar condiciones de control de flujo (AEAT)
- Crear lotes y asociar registros
- Actualizar contadores de instalación

NO gestiona:
- Transacciones (commit/rollback)
- Locks distribuidos
- Encolado de tareas
- Eventos outbox (responsabilidad del orquestador)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.models.models import (
    EstadoRegistroFacturacion,
    InstalacionSIF,
    LoteEnvio,
    RegistroFacturacion,
)

logger = logging.getLogger(__name__)


class LoteService:
    """
    Servicio de dominio puro: solo lógica de negocio.

    El caller (orquestador) es responsable de:
    - Gestionar transacciones (commit/rollback)
    - Adquirir/liberar locks distribuidos
    - Crear eventos outbox
    """

    def __init__(self, db: Session):
        self.db = db

    def crear_lote_para_instalacion(
        self,
        instalacion_sif_id: int,
        max_registros: int = 1000,
    ) -> Optional[LoteEnvio]:
        """
        Crea un lote si se cumplen las condiciones de control de flujo AEAT.

        Args:
            instalacion_sif_id: ID de la instalación
            max_registros: Límite máximo de registros por lote (AEAT: 1000)

        Returns:
            LoteEnvio si se creó exitosamente
            None si no se cumplen las condiciones

        Raises:
            SQLAlchemyError: Errores de base de datos

        IMPORTANTE:
        - NO hace commit (usa flush() para obtener IDs)
        - El caller DEBE tener lock de Redis adquirido
        - El caller DEBE hacer commit/rollback
        - El caller DEBE crear evento outbox en la MISMA transacción

        Veri-factu_Descripcion_SWeb.pdf 6.4.4.1: Mecanismo de control de flujo
        """
        # Verificar condiciones de control de flujo (AEAT)
        instalacion = self._control_flujo(instalacion_sif_id, max_registros)
        if not instalacion:
            logger.debug(
                f"Instalación {instalacion_sif_id} no cumple condiciones de flujo"
            )
            return None

        # Seleccionar registros pendientes con row-level lock
        # FOR UPDATE SKIP LOCKED: evita bloqueos, solo toma registros disponibles
        registros = (
            self.db.execute(
                select(RegistroFacturacion)
                .where(
                    RegistroFacturacion.instalacion_sif_id == instalacion_sif_id,
                    RegistroFacturacion.estado == EstadoRegistroFacturacion.PENDIENTE,
                )
                .order_by(RegistroFacturacion.created_at)
                .limit(max_registros)
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )

        if not registros:
            logger.debug(
                f"No hay registros disponibles para instalación {instalacion_sif_id}"
            )
            return None

        # Crear lote
        lote = LoteEnvio(
            instalacion_sif_id=instalacion_sif_id,
            num_registros=len(registros),
            xml_enviado="",  # Se generará en worker_aeat
            tiempo_espera_recibido=None,  # Se actualizará tras respuesta AEAT
            proximo_envio_permitido_at=None,  # Se actualizará tras respuesta AEAT
        )

        self.db.add(lote)
        self.db.flush()  # Obtener ID del lote sin commitear

        # Asociar registros al lote y marcarlos como ENCOLADO
        registro_ids = [r.id for r in registros]
        self.db.execute(
            update(RegistroFacturacion)
            .where(RegistroFacturacion.id.in_(registro_ids))
            .values(
                lote_envio_id=lote.id,
                estado=EstadoRegistroFacturacion.ENCOLADO,
            )
        )

        # Decrementar contador de pendientes en la instalación
        encolados = len(registros)
        self.db.execute(
            update(InstalacionSIF)
            .where(InstalacionSIF.id == instalacion_sif_id)
            .values(
                registros_pendientes=InstalacionSIF.registros_pendientes
                - encolados
                # ultimo_envio_at se actualizará tras respuesta de AEAT
            )
        )

        logger.info(
            f"Lote {lote.id} creado para instalación {instalacion_sif_id} "
            f"con {encolados} registros (flush ejecutado, pendiente commit)"
        )

        return lote

    def control_flujo(self, instalacion_sif_id: int, max_registros: int = 1000) -> bool:
        """
        Versión pública de control_flujo para el scheduler ligero.

        Returns:
            True si cumple condiciones para crear lote
            False si no cumple condiciones
        """
        instalacion = self._control_flujo(instalacion_sif_id, max_registros)
        return instalacion is not None

    def _control_flujo(
        self, instalacion_sif_id: int, max_registros: int
    ) -> Optional[InstalacionSIF]:
        """
        Verifica si se cumplen las condiciones para enviar lote a AEAT.

        Normativa AEAT (Veri-factu_Descripcion_SWeb.pdf 6.4.4.1):
        El sistema enviará cuando ocurra lo primero de:
        1. Acumulación de ≥1000 registros PENDIENTES
        2. Transcurso del tiempo 't' desde último envío (+10% margen seguridad)

        Args:
            instalacion_sif_id: ID de la instalación
            max_registros: Límite de registros (normalmente 1000)

        Returns:
            InstalacionSIF si cumple condiciones
            None si no cumple o no existe
        """
        instalacion = self.db.get(InstalacionSIF, instalacion_sif_id)
        if not instalacion:
            logger.warning(f"Instalación {instalacion_sif_id} no encontrada")
            return None

        ahora = datetime.now(timezone.utc)

        # Condición 1: Límite de registros alcanzado (≥1000)
        max_registros_acumulados = instalacion.registros_pendientes >= max_registros

        # Condición 2: Tiempo de espera 't' cumplido (con margen de seguridad)
        tiempo_cumplido = False
        tiempo_transcurrido = None

        if instalacion.ultimo_envio_at:
            # Aplicar margen de seguridad: mayor entre +10% y +5 segundos
            tiempo_espera_seguro = max(
                instalacion.ultimo_tiempo_espera * 1.1,  # +10% margen
                instalacion.ultimo_tiempo_espera + 5,  # +5s mínimo absoluto
            )
            tiempo_transcurrido = (ahora - instalacion.ultimo_envio_at).total_seconds()
            tiempo_cumplido = tiempo_transcurrido >= tiempo_espera_seguro

            logger.debug(
                f"Instalación {instalacion_sif_id}: "
                f"tiempo_transcurrido={tiempo_transcurrido:.1f}s, "
                f"tiempo_espera_seguro={tiempo_espera_seguro:.1f}s, "
                f"cumplido={tiempo_cumplido}"
            )
        else:
            # Primera vez: siempre permitir (respetando límite de registros)
            tiempo_cumplido = True
            logger.debug(f"Instalación {instalacion_sif_id}: primer envío permitido")

        # CRÍTICO: Si hay registros pero NO se cumple ninguna condición, NO enviar
        if not (max_registros_acumulados or tiempo_cumplido):
            logger.debug(
                f"Instalación {instalacion_sif_id} NO cumple condiciones: "
                f"pendientes={instalacion.registros_pendientes}/{max_registros}, "
                f"tiempo_transcurrido={tiempo_transcurrido or 0:.1f}s/"
                f"{instalacion.ultimo_tiempo_espera}s"
            )
            return None

        # Verificación adicional: ¿realmente hay registros PENDIENTES en BD?
        count_pendientes = self.db.scalar(
            select(func.count()).where(
                RegistroFacturacion.instalacion_sif_id == instalacion_sif_id,
                RegistroFacturacion.estado == EstadoRegistroFacturacion.PENDIENTE,
            )
        )

        if count_pendientes == 0:
            # Inconsistencia detectada: el contador no coincide con la realidad
            logger.warning(
                f"⚠️ Inconsistencia en instalación {instalacion_sif_id}: "
                f"contador={instalacion.registros_pendientes}, real={count_pendientes}."
                f"Corrigiendo contador..."
            )
            self.db.execute(
                update(InstalacionSIF)
                .where(InstalacionSIF.id == instalacion_sif_id)
                .values(registros_pendientes=0)
            )
            # NO hacer commit aquí - el caller lo hará
            return None

        logger.info(
            f"✅ Instalación {instalacion_sif_id} cumple condiciones: "
            f"pendientes={instalacion.registros_pendientes}, "
            f"max_acumulados={max_registros_acumulados}, "
            f"tiempo_cumplido={tiempo_cumplido}"
        )

        return instalacion
