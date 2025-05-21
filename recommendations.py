from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
from typing import Dict, List
from database_model import CardioHealth


class RecommendationSystem:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'age', 'gender', 'height', 'weight',
            'ap_hi', 'ap_lo', 'cholesterol',
            'gluc', 'smoke', 'alco', 'active'
        ]

    def is_trained(self) -> bool:
        """Verifica si el modelo ya fue entrenado"""
        return self.model is not None

    async def train_model(self, records: List[CardioHealth]):
        """Entrena el modelo RandomForest con registros de Clever"""
        if len(records) < 100:
            raise ValueError("Se necesitan mínimo 100 registros para entrenar el modelo")

        data = pd.DataFrame([{
            'age': r.age,
            'gender': r.gender,
            'height': r.height,
            'weight': r.weight,
            'ap_hi': r.ap_hi,
            'ap_lo': r.ap_lo,
            'cholesterol': r.cholesterol,
            'gluc': r.gluc,
            'smoke': r.smoke,
            'alco': r.alco,
            'active': r.active,
            'cardio': r.cardio
        } for r in records])

        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42
        )
        self.model.fit(data[self.feature_names], data['cardio'])

    def generate_recommendations(self, patient: CardioHealth) -> Dict:
        """Genera todas las recomendaciones y métricas"""
        features = pd.DataFrame([{
            'age': patient.age,
            'gender': patient.gender,
            'height': patient.height,
            'weight': patient.weight,
            'ap_hi': patient.ap_hi,
            'ap_lo': patient.ap_lo,
            'cholesterol': patient.cholesterol,
            'gluc': patient.gluc,
            'smoke': patient.smoke,
            'alco': patient.alco,
            'active': patient.active
        }])

        proba = self.model.predict_proba(features)[0][1]

        return {
            "risk_data": self._get_risk_data(proba),
            "key_factors": self._get_key_factors(features),
            "health_metrics": self._calculate_health_metrics(patient),
            "recommendations": self._generate_all_recommendations(patient, proba)
        }

    def _get_risk_data(self, probability: float) -> Dict:
        if probability > 0.8:
            return {"level": "Extremo", "color": "#FF0000"}
        elif probability > 0.6:
            return {"level": "Alto", "color": "#FF6B00"}
        elif probability > 0.4:
            return {"level": "Moderado", "color": "#FFC100"}
        else:
            return {"level": "Bajo", "color": "#00B050"}

    def _get_key_factors(self, features: pd.DataFrame) -> List[Dict]:
        importances = self.model.feature_importances_
        top_indices = np.argsort(importances)[-3:][::-1]
        return [{
            "factor": self.feature_names[i],
            "importance": round(float(importances[i]), 4),
            "value": float(features.iloc[0][i])
        } for i in top_indices]

    def _calculate_health_metrics(self, patient: CardioHealth) -> Dict:
        """Calcula métricas de salud incluyendo IMC, categoría de presión arterial y edad metabólica"""
        # Convertir altura de cm a metros para el cálculo del IMC
        altura_metros = patient.height / 100
        # Calcular IMC: peso(kg) / altura²(m)
        imc = patient.weight / (altura_metros ** 2)
        
        # Clasificación de presión arterial según guías internacionales
        presion_arterial = self._classify_blood_pressure(patient.ap_hi, patient.ap_lo)
        
        # Cálculo de edad metabólica considerando diversos factores
        edad_base = patient.age  # ya está en días
        edad_metabolica = edad_base

        # Ajustes por IMC
        if imc >= 30:  # Obesidad
            edad_metabolica += 1825  # +5 años en días
        elif imc >= 25:  # Sobrepeso
            edad_metabolica += 730  # +2 años en días
        elif imc < 18.5:  # Bajo peso
            edad_metabolica += 365  # +1 año en días

        # Ajustes por presión arterial
        if patient.ap_hi >= 140 or patient.ap_lo >= 90:  # Hipertensión
            edad_metabolica += 1460  # +4 años en días
        elif patient.ap_hi >= 130 or patient.ap_lo >= 85:  # Pre-hipertensión
            edad_metabolica += 730  # +2 años en días

        # Ajustes por colesterol
        if patient.cholesterol == 3:  # Muy alto
            edad_metabolica += 1825  # +5 años en días
        elif patient.cholesterol == 2:  # Alto
            edad_metabolica += 730  # +2 años en días

        # Ajustes por glucosa
        if patient.gluc == 3:  # Muy alta
            edad_metabolica += 1460  # +4 años en días
        elif patient.gluc == 2:  # Alta
            edad_metabolica += 730  # +2 años en días

        # Ajustes por estilo de vida
        if patient.smoke:  # Fumador
            edad_metabolica += 1825  # +5 años en días
        if patient.alco:  # Consumo de alcohol
            edad_metabolica += 730  # +2 años en días
        if not patient.active:  # Sedentarismo
            edad_metabolica += 1095  # +3 años en días

        return {
            "imc": round(imc, 1),
            "imc_category": self._classify_imc(imc),
            "blood_pressure": presion_arterial,
            "metabolic_age": edad_metabolica  # en días
        }

    def _generate_all_recommendations(self, patient: CardioHealth, probability: float) -> List[str]:
        """Genera todas las recomendaciones detalladas"""
        recommendations = []
        imc = patient.weight / (patient.height ** 2)
        factors = [f["factor"] for f in self._get_key_factors(pd.DataFrame([{
            'age': patient.age,
            'gender': patient.gender,
            'height': patient.height,
            'weight': patient.weight,
            'ap_hi': patient.ap_hi,
            'ap_lo': patient.ap_lo,
            'cholesterol': patient.cholesterol,
            'gluc': patient.gluc,
            'smoke': patient.smoke,
            'alco': patient.alco,
            'active': patient.active
        }]))]

        # 1. Recomendaciones por nivel de riesgo
        if probability > 0.8:
            recommendations.extend([
                "🚨 EMERGENCIA: Riesgo cardiovascular extremadamente alto (>80%)",
                "🩺 Consulte a un cardiólogo dentro de las próximas 48 horas",
                "📞 Contacte a su médico de cabecera inmediatamente"
            ])
        elif probability > 0.6:
            recommendations.extend([
                "⚠️ ALERTA: Riesgo cardiovascular alto (60-80%)",
                "🩺 Programe cita con cardiólogo en los próximos 7 días",
                "📝 Realice monitoreo diario de presión arterial"
            ])

        # 2. Recomendaciones por factores clave
        for factor in factors:
            if factor == 'ap_hi' and patient.ap_hi > 140:
                recommendations.extend([
                    "💊 Presión arterial elevada: Tome sus medicamentos puntualmente",
                    "🧂 Reduzca consumo de sal a menos de 5g/día",
                    "📉 Objetivo: Menos de 135/85 mmHg en casa"
                ])

            elif factor == 'cholesterol':
                if patient.cholesterol == 3:
                    recommendations.extend([
                        "🩸 Colesterol muy elevado: Requiere tratamiento farmacológico",
                        "🍳 Elimine grasas trans y saturadas de su dieta",
                        "💊 Posible necesidad de estatinas (consulte a su médico)"
                    ])
                else:
                    recommendations.extend([
                        "🥑 Aumente consumo de grasas saludables (aguacate, nueces)",
                        "🏃‍♂️ Ejercicio aeróbico 4x/semana para mejorar perfil lipídico"
                    ])

        # 3. Recomendaciones por IMC
        if imc >= 30:
            recommendations.extend([
                "⚖️ Obesidad: Pérdida de peso prioritaria (5-10% en 6 meses)",
                "🍽️ Consulte a nutricionista para plan personalizado",
                "🚶‍♂️ Caminatas diarias de 45 minutos como mínimo"
            ])
        elif imc >= 25:
            recommendations.extend([
                "⚖️ Sobrepeso: Evite ganar más peso",
                "🥗 Reduzca porciones y aumente vegetales",
                "🏋️‍♂️ Combine cardio y entrenamiento de fuerza"
            ])

        # 4. Hábitos específicos
        if patient.smoke == 1:
            recommendations.extend([
                "🚭 Tabaquismo: Programa de cesación tabáquica URGENTE",
                "📱 Descargue app 'Dejar de Fumar' del Ministerio de Salud",
                "☎️ Llame a la línea de ayuda 123-456-7890"
            ])

        if patient.active == 0:
            recommendations.extend([
                "🏃‍♂️ Sedentarismo: Comience con 10 minutos diarios de ejercicio",
                "⏰ Use podómetro: Meta 8,000 pasos/día",
                "🪑 Levantarse cada 30 minutos si trabaja sentado"
            ])

        # 5. Recomendaciones generales
        recommendations.extend([
            "💧 Hidratación: 2L de agua/día (excepto contraindicación médica)",
            "😌 Manejo de estrés: Técnicas de respiración 5 min/día",
            "🛌 Sueño: 7-9 horas/noche en horario regular"
        ])

        return recommendations

    def _classify_imc(self, imc: float) -> str:
        """Clasifica el IMC según rangos estándar de la OMS"""
        if imc < 16:
            return "Delgadez Severa"
        elif imc < 17:
            return "Delgadez Moderada"
        elif imc < 18.5:
            return "Delgadez Leve"
        elif imc < 25:
            return "Normal"
        elif imc < 30:
            return "Sobrepeso"
        elif imc < 35:
            return "Obesidad Grado 1"
        elif imc < 40:
            return "Obesidad Grado 2"
        else:
            return "Obesidad Grado 3"

    def _classify_blood_pressure(self, systolic: int, diastolic: int) -> str:
        """Clasifica la presión arterial según valores estándar"""
        if systolic >= 180 or diastolic >= 110:
            return "Hipertensión Crisis"
        elif systolic >= 160 or diastolic >= 100:
            return "Hipertensión Grado 2"
        elif systolic >= 140 or diastolic >= 90:
            return "Hipertensión Grado 1"
        elif systolic >= 130 or diastolic >= 85:
            return "Pre-hipertensión"
        elif systolic >= 120 or diastolic >= 80:
            return "Normal Alta"
        else:
            return "Normal"

    def _calculate_metabolic_age(self, patient: CardioHealth) -> int:
        edad_base = patient.age
        imc = patient.weight / (patient.height ** 2)

        if imc > 30:
            edad_base += 10
        elif imc > 25:
            edad_base += 5
        if patient.active == 0: edad_base += 5

        return min(max(edad_base, patient.age), 100)

recommendation_system = RecommendationSystem()