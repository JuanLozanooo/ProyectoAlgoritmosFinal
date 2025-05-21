from typing import Optional, Dict, List
from sqlmodel import select
from sqlalchemy import func
from sqlmodel.ext.asyncio.session import AsyncSession
from database_model import CardioHealth
from recommendations import RecommendationSystem, recommendation_system

from fastapi import HTTPException


class CardioHealthOperations:
    @staticmethod
    async def get_all_records(
            session: AsyncSession,
            page: int = 1,
            per_page: int = 100
    ) -> dict:
        """Obtiene registros paginados para mostrar en tablas"""
        offset = (page - 1) * per_page
        query = select(CardioHealth).offset(offset).limit(per_page)
        result = await session.execute(query)

        # Contar total de registros (para paginación)
        total_query = select(func.count()).select_from(CardioHealth)
        total = (await session.execute(total_query)).scalar_one()

        return {
            "data": result.scalars().all(),
            "total": total,
            "page": page,
            "per_page": per_page
        }

    @staticmethod
    async def get_record_by_id(session: AsyncSession, record_id: int) -> Optional[CardioHealth]:
        """Obtiene un registro por su ID"""
        return await session.get(CardioHealth, record_id)

    @staticmethod
    async def add_record(session: AsyncSession, record_data: Dict) -> CardioHealth:
        """Agrega un nuevo registro a la base de datos"""
        # Asegurarse de que no se incluya el ID
        if 'id' in record_data:
            del record_data['id']
        
        new_record = CardioHealth(**record_data)
        session.add(new_record)
        await session.commit()
        await session.refresh(new_record)
        return new_record

    @staticmethod
    async def edit_record(session: AsyncSession, record_id: int, update_data: Dict) -> Optional[CardioHealth]:
        """Edita un registro existente"""
        record = await session.get(CardioHealth, record_id)
        if not record:
            return None

        for key, value in update_data.items():
            setattr(record, key, value)

        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def get_recommendations(session: AsyncSession, record_id: int) -> Dict:
        """Obtiene recomendaciones personalizadas basadas en IA para un paciente"""
        try:
            # 1. Obtener paciente
            patient = await session.get(CardioHealth, record_id)
            if not patient:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró paciente con ID {record_id}"
                )

            # 2. Entrenar modelo si es necesario
            if not recommendation_system.is_trained():
                result = await session.execute(select(CardioHealth))
                records = result.scalars().all()

                if len(records) < 100:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Se necesitan mínimo 100 registros (actual: {len(records)})"
                    )

                await recommendation_system.train_model([CardioHealth(**r.__dict__) for r in records])

            # 3. Generar recomendaciones
            patient_data = CardioHealth(**patient.__dict__)
            recommendations = recommendation_system.generate_recommendations(patient_data)

            return {
                "success": True,
                "data": recommendations,
                "message": "Recomendaciones generadas exitosamente"
            }

        except HTTPException:
            raise  # Re-lanzamos las excepciones HTTP que ya manejamos

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generando recomendaciones: {str(e)}"
            )