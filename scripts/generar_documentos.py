"""Genera la base documental de Clínica VidaSana (5 PDFs + 1 CSV).

Los archivos resultantes viven en `data/` y son la única fuente de verdad del
agente. El script es idempotente: se puede volver a ejecutar para regenerar
los documentos desde cero.

    python scripts/generar_documentos.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

RAIZ = Path(__file__).resolve().parent.parent
DIRECTORIO_DATOS = RAIZ / "data"

# Los PDFs viven en un repositorio publico y pueden descargarse sueltos, fuera
# del contexto del README. El aviso viaja dentro de cada documento para que
# nadie los confunda con la documentacion de un centro de salud real.
AVISO_FICCION = (
    "<b>DOCUMENTO FICTICIO — MATERIAL DE DEMOSTRACIÓN.</b> Clínica VidaSana S.A.C. es una "
    "empresa inventada, creada como base de conocimiento para un proyecto académico del "
    "programa Oracle Next Education (Challenge Alura Agente). Los nombres, direcciones, "
    "teléfonos, correos, precios y políticas de este documento son ficticios: no "
    "corresponden a ningún establecimiento de salud real ni deben usarse para tomar "
    "decisiones médicas, legales o administrativas."
)


# --------------------------------------------------------------------------- #
# Contenido de los documentos
# --------------------------------------------------------------------------- #

DOCUMENTOS: dict[str, dict] = {
    "01_Politica_de_Privacidad_y_Datos_del_Paciente.pdf": {
        "titulo": "Política de Privacidad y Protección de Datos del Paciente",
        "subtitulo": "Clínica VidaSana S.A.C. — Versión 4.2 — Vigente desde el 01 de marzo de 2026",
        "secciones": [
            (
                "1. Objetivo y alcance",
                [
                    "La presente política regula el tratamiento de los datos personales y de la información "
                    "clínica de los pacientes de Clínica VidaSana S.A.C. (en adelante, VidaSana), en el marco "
                    "de la Ley N.º 29733, Ley de Protección de Datos Personales, y su Reglamento.",
                    "Aplica a las tres sedes de la clínica (San Isidro, Miraflores y Surco), al portal web, "
                    "a la aplicación móvil VidaSana App y a los canales de atención telefónica y WhatsApp.",
                ],
            ),
            (
                "2. Datos que recolectamos",
                [
                    "VidaSana recolecta tres categorías de datos: (a) datos de identificación (nombres, "
                    "documento de identidad, fecha de nacimiento, dirección, teléfono y correo electrónico); "
                    "(b) datos sensibles de salud (historia clínica, diagnósticos, resultados de laboratorio "
                    "e imágenes médicas); y (c) datos de facturación (medio de pago, comprobantes y "
                    "convenio o seguro asociado).",
                    "Los datos sensibles de salud solo se recolectan con consentimiento expreso, previo, "
                    "informado y por escrito del paciente o de su representante legal, salvo en situaciones "
                    "de emergencia médica donde exista riesgo para la vida.",
                ],
            ),
            (
                "3. Plazos de conservación",
                [
                    "La historia clínica se conserva por un plazo mínimo de quince (15) años contados desde "
                    "la última atención del paciente, conforme a la Norma Técnica de Salud para la Gestión "
                    "de la Historia Clínica.",
                    "Las imágenes médicas (radiografías, tomografías y resonancias) se conservan por diez "
                    "(10) años. Los registros de facturación se conservan por cinco (5) años.",
                    "Las grabaciones de videovigilancia de las áreas comunes se conservan por treinta (30) "
                    "días calendario y luego se eliminan de forma automática e irreversible.",
                ],
            ),
            (
                "4. Derechos ARCO del paciente",
                [
                    "Todo paciente puede ejercer sus derechos de Acceso, Rectificación, Cancelación y "
                    "Oposición (ARCO) enviando una solicitud al correo datospersonales@vidasana.pe o "
                    "presentándola en la Plataforma de Atención al Usuario de cualquiera de nuestras sedes.",
                    "El plazo máximo de respuesta es de veinte (20) días hábiles para el derecho de acceso "
                    "y de diez (10) días hábiles para los derechos de rectificación, cancelación y "
                    "oposición, contados desde la recepción de la solicitud.",
                    "La entrega de una copia de la historia clínica es gratuita una (1) vez al año. Las "
                    "copias adicionales tienen un costo administrativo de S/ 25.00 por historia.",
                ],
            ),
            (
                "5. Compartición de información con terceros",
                [
                    "VidaSana comparte información clínica únicamente con: aseguradoras y entidades con "
                    "convenio vigente para fines de autorización y liquidación de coberturas; laboratorios "
                    "de referencia para el procesamiento de muestras; y autoridades sanitarias o judiciales "
                    "cuando exista un mandato legal expreso.",
                    "VidaSana no comercializa, cede ni transfiere datos de pacientes con fines publicitarios "
                    "o comerciales bajo ninguna circunstancia.",
                ],
            ),
            (
                "6. Medidas de seguridad",
                [
                    "La información clínica se almacena cifrada en reposo con AES-256 y en tránsito con "
                    "TLS 1.3. El acceso al sistema de historias clínicas requiere autenticación de doble "
                    "factor y está restringido por perfil de rol.",
                    "Todo acceso a una historia clínica queda registrado en una bitácora de auditoría "
                    "inalterable que consigna usuario, fecha, hora y motivo de consulta.",
                    "Ante un incidente de seguridad que comprometa datos personales, VidaSana notificará al "
                    "paciente afectado y a la Autoridad Nacional de Protección de Datos Personales dentro "
                    "de las cuarenta y ocho (48) horas de detectado el evento.",
                ],
            ),
            (
                "7. Canal de contacto del Oficial de Protección de Datos",
                [
                    "Oficial de Protección de Datos: correo datospersonales@vidasana.pe, teléfono "
                    "(01) 612-8800 anexo 240, de lunes a viernes de 08:00 a 18:00 horas.",
                ],
            ),
        ],
    },
    "02_Politica_de_Cancelaciones_y_Reagendamiento.pdf": {
        "titulo": "Política de Cancelaciones, Reagendamiento y No Asistencia",
        "subtitulo": "Clínica VidaSana S.A.C. — Versión 3.0 — Vigente desde el 15 de enero de 2026",
        "secciones": [
            (
                "1. Cancelación de citas",
                [
                    "El paciente puede cancelar una cita sin costo alguno hasta veinticuatro (24) horas "
                    "antes de la hora programada, a través de la VidaSana App, del portal web, de la "
                    "central telefónica (01) 612-8800 o del WhatsApp oficial +51 987 654 321.",
                    "Las cancelaciones realizadas con menos de 24 horas de anticipación generan un cargo "
                    "administrativo equivalente al 30% del valor de la consulta, que se aplica al momento "
                    "de agendar la siguiente cita.",
                    "Los procedimientos ambulatorios y las cirugías menores requieren una anticipación de "
                    "cuarenta y ocho (48) horas para cancelar sin penalidad.",
                ],
            ),
            (
                "2. Reagendamiento",
                [
                    "El reagendamiento es gratuito e ilimitado siempre que se solicite con al menos 24 "
                    "horas de anticipación. Cada cita admite un máximo de tres (3) reagendamientos; a "
                    "partir del cuarto cambio el sistema exige agendar una cita nueva.",
                    "El reagendamiento mantiene el precio original de la consulta durante sesenta (60) "
                    "días calendario, aunque la tarifa de la especialidad haya variado en ese periodo.",
                ],
            ),
            (
                "3. Inasistencia sin aviso (no-show)",
                [
                    "Se considera inasistencia sin aviso cuando el paciente no se presenta ni cancela la "
                    "cita. La primera inasistencia genera únicamente una notificación de advertencia.",
                    "La segunda inasistencia en un periodo de seis (6) meses genera un cargo del 50% del "
                    "valor de la consulta. A partir de la tercera inasistencia, el paciente queda "
                    "habilitado a agendar solo con pago adelantado del 100% durante los siguientes "
                    "noventa (90) días.",
                    "Los cargos por inasistencia se anulan si el paciente acredita una emergencia médica, "
                    "un accidente o el fallecimiento de un familiar directo, presentando el sustento "
                    "dentro de los siete (7) días calendario posteriores a la cita perdida.",
                ],
            ),
            (
                "4. Tolerancia de llegada",
                [
                    "La tolerancia de llegada es de quince (15) minutos para consultas ambulatorias. "
                    "Pasado ese tiempo, la atención queda sujeta a la disponibilidad del profesional y "
                    "puede ser reprogramada sin penalidad para el paciente.",
                    "Para procedimientos de imagenología y laboratorio no existe tolerancia, dado que los "
                    "bloques son de agenda cerrada. Se recomienda llegar veinte (20) minutos antes.",
                ],
            ),
            (
                "5. Cancelaciones por parte de la clínica",
                [
                    "Si VidaSana cancela o reprograma una cita por indisponibilidad del profesional, el "
                    "paciente recibe la notificación con al menos 12 horas de anticipación y accede a: "
                    "reagendamiento prioritario en las siguientes 72 horas, o la devolución íntegra del "
                    "monto pagado dentro de los cinco (5) días hábiles.",
                    "Adicionalmente, VidaSana otorga un descuento del 20% sobre la consulta reprogramada "
                    "como compensación por la molestia ocasionada.",
                ],
            ),
            (
                "6. Devoluciones",
                [
                    "Las devoluciones se procesan al mismo medio de pago utilizado originalmente. El plazo "
                    "es de cinco (5) días hábiles para tarjetas de débito y hasta quince (15) días hábiles "
                    "para tarjetas de crédito, según los tiempos del emisor.",
                    "Las devoluciones en efectivo se realizan en la caja de la sede donde se generó el "
                    "pago, presentando el comprobante original y el documento de identidad del titular.",
                ],
            ),
        ],
    },
    "03_Guia_de_Convenios_y_Coberturas_Medicas.pdf": {
        "titulo": "Guía de Convenios, Seguros y Coberturas Médicas",
        "subtitulo": "Clínica VidaSana S.A.C. — Versión 2.5 — Vigente desde el 01 de febrero de 2026",
        "secciones": [
            (
                "1. Convenios vigentes",
                [
                    "VidaSana mantiene convenio directo con las siguientes entidades: Rímac Seguros, "
                    "Pacífico Salud, La Positiva Sanitas, Mapfre Perú, EPS Sanitas y el Seguro Integral "
                    "de Salud (SIS) en la modalidad de intercambio prestacional.",
                    "El convenio corporativo VidaSana Empresas aplica a colaboradores de las empresas "
                    "afiliadas y otorga un 25% de descuento sobre el tarifario particular en consultas "
                    "ambulatorias y un 15% en procedimientos de imagenología.",
                ],
            ),
            (
                "2. Cobertura y copagos",
                [
                    "El copago de consulta ambulatoria para pacientes con Rímac Seguros y Pacífico Salud "
                    "es de S/ 35.00 en medicina general y S/ 50.00 en especialidades. Para La Positiva "
                    "Sanitas y Mapfre Perú el copago es de S/ 40.00 y S/ 55.00 respectivamente.",
                    "El deducible anual, cuando aplica, corre por cuenta del asegurado y debe estar "
                    "cubierto antes de que la aseguradora asuma el porcentaje de cobertura pactado.",
                    "Los procedimientos estéticos, los chequeos preocupacionales y la medicina alternativa "
                    "no están cubiertos por ningún convenio y se facturan a tarifa particular.",
                ],
            ),
            (
                "3. Requisitos de atención con seguro",
                [
                    "Para atenderse con seguro el paciente debe presentar: documento de identidad vigente, "
                    "carné o código de asegurado, y la carta de garantía cuando el procedimiento la exija.",
                    "La autorización de la aseguradora se tramita en la Plataforma de Convenios de la sede. "
                    "El tiempo estimado de respuesta es de veinte (20) minutos para consultas ambulatorias "
                    "y de hasta cuarenta y ocho (48) horas para procedimientos programados.",
                    "Si la aseguradora rechaza la cobertura, el paciente puede optar por la tarifa "
                    "particular o reprogramar sin costo.",
                ],
            ),
            (
                "4. Programa de fidelidad VidaSana Plus",
                [
                    "VidaSana Plus es el programa de membresía anual de la clínica. Tiene un costo de "
                    "S/ 390.00 al año por titular y S/ 240.00 por cada dependiente directo.",
                    "Beneficios: 30% de descuento en consultas ambulatorias particulares, 20% en "
                    "laboratorio e imagenología, dos (2) chequeos preventivos anuales sin costo, atención "
                    "preferente en la agenda y teleconsulta ilimitada de medicina general.",
                    "La membresía se activa a las 24 horas del pago y no tiene periodo de carencia para "
                    "consultas ambulatorias. Para procedimientos programados existe una carencia de "
                    "treinta (30) días calendario.",
                ],
            ),
            (
                "5. Facturación y comprobantes",
                [
                    "VidaSana emite boleta electrónica o factura electrónica al correo registrado del "
                    "paciente dentro de las dos (2) horas posteriores a la atención.",
                    "Para emitir factura es indispensable proporcionar el RUC y la razón social antes de "
                    "efectuar el pago. No se realizan cambios de boleta a factura después de emitido el "
                    "comprobante.",
                    "Medios de pago aceptados: efectivo, tarjetas de débito y crédito Visa, Mastercard, "
                    "American Express y Diners, Yape, Plin y transferencia bancaria.",
                ],
            ),
        ],
    },
    "04_Instrucciones_Pre_y_Post_Consulta.pdf": {
        "titulo": "Instrucciones de Preparación Pre y Post Consulta",
        "subtitulo": "Clínica VidaSana S.A.C. — Versión 5.1 — Vigente desde el 10 de abril de 2026",
        "secciones": [
            (
                "1. Preparación general para consulta ambulatoria",
                [
                    "Presentarse quince (15) minutos antes de la hora agendada con documento de identidad "
                    "vigente. Traer los exámenes previos, informes médicos y la lista actualizada de "
                    "medicamentos que consume, incluyendo dosis y frecuencia.",
                    "Los pacientes menores de dieciocho (18) años deben acudir acompañados por su padre, "
                    "madre o apoderado acreditado con documento de identidad.",
                ],
            ),
            (
                "2. Análisis de laboratorio",
                [
                    "Perfil lipídico y glucosa en ayunas: ayuno estricto de doce (12) horas. Se permite "
                    "beber agua. Suspender el consumo de alcohol cuarenta y ocho (48) horas antes.",
                    "Perfil hepático y hemograma completo: ayuno de ocho (8) horas.",
                    "Examen completo de orina: recolectar la primera orina de la mañana, descartando el "
                    "primer chorro, en el frasco estéril entregado por la clínica. Entregar la muestra "
                    "dentro de las dos (2) horas de recolectada.",
                    "Prueba de tolerancia a la glucosa: ayuno de diez (10) horas y permanencia en la sede "
                    "durante todo el examen, que dura aproximadamente dos (2) horas.",
                    "Los resultados de laboratorio se publican en la VidaSana App en un plazo de "
                    "veinticuatro (24) horas para pruebas de rutina y de hasta cinco (5) días hábiles para "
                    "pruebas especializadas.",
                ],
            ),
            (
                "3. Estudios de imagenología",
                [
                    "Ecografía abdominal completa: ayuno de ocho (8) horas. No consumir bebidas gaseosas "
                    "el día previo.",
                    "Ecografía pélvica o transvaginal: acudir con la vejiga llena; beber un (1) litro de "
                    "agua una hora antes del examen y no orinar hasta finalizado el estudio.",
                    "Tomografía con contraste: ayuno de seis (6) horas, análisis de creatinina con una "
                    "antigüedad no mayor a treinta (30) días, y declaración de alergias a medios de "
                    "contraste yodados.",
                    "Resonancia magnética: no ingresar con objetos metálicos, prótesis removibles ni "
                    "tarjetas magnéticas. Los portadores de marcapasos, implantes cocleares o clips "
                    "vasculares deben informarlo al agendar, ya que puede contraindicar el estudio.",
                    "Radiografía: no requiere preparación previa. Las pacientes gestantes o con sospecha "
                    "de embarazo deben informarlo antes del estudio.",
                ],
            ),
            (
                "4. Indicaciones post consulta",
                [
                    "La receta electrónica se envía al correo del paciente y queda disponible en la "
                    "VidaSana App. Tiene una vigencia de treinta (30) días calendario desde su emisión.",
                    "La primera consulta de control dentro de los treinta (30) días posteriores tiene un "
                    "costo del 50% de la tarifa de la consulta original, siempre que sea con el mismo "
                    "profesional y por el mismo motivo.",
                    "Las interconsultas derivadas se agendan directamente en la Plataforma de Atención al "
                    "Usuario o mediante la App, sin necesidad de una nueva consulta de medicina general.",
                ],
            ),
            (
                "5. Teleconsulta",
                [
                    "La teleconsulta se realiza por videollamada a través de la VidaSana App. El enlace se "
                    "habilita diez (10) minutos antes de la hora agendada.",
                    "Se recomienda conexión a internet estable de al menos 5 Mbps, un ambiente iluminado y "
                    "privado, y tener a la mano los exámenes previos en formato digital.",
                    "La teleconsulta no aplica para primeras consultas de pediatría menores de un (1) año, "
                    "ni para cuadros que requieran examen físico presencial, ni para emergencias.",
                ],
            ),
            (
                "6. Emergencias",
                [
                    "El servicio de emergencia de la sede San Isidro atiende las 24 horas, todos los días "
                    "del año. Las sedes Miraflores y Surco atienden urgencias de 07:00 a 22:00 horas.",
                    "En caso de emergencia con riesgo vital, comunicarse con la línea de emergencia "
                    "(01) 612-8899 o acudir directamente a la sede San Isidro.",
                ],
            ),
        ],
    },
    "05_Preguntas_Frecuentes_VidaSana.pdf": {
        "titulo": "Preguntas Frecuentes (FAQ) — Pacientes",
        "subtitulo": "Clínica VidaSana S.A.C. — Actualizado al 01 de julio de 2026",
        "secciones": [
            (
                "Agendamiento y atención",
                [
                    "¿Cómo agendo una cita? A través de la VidaSana App, del portal web vidasana.pe, de la "
                    "central telefónica (01) 612-8800 o presencialmente en la Plataforma de Atención al "
                    "Usuario de cualquiera de las tres sedes.",
                    "¿Con cuánta anticipación puedo agendar? La agenda se abre con sesenta (60) días "
                    "calendario de anticipación y hasta dos (2) horas antes de la cita, según "
                    "disponibilidad del profesional.",
                    "¿Necesito orden médica para un examen de laboratorio? Sí para los exámenes cubiertos "
                    "por seguro. En modalidad particular, los perfiles preventivos de rutina se pueden "
                    "tomar sin orden médica.",
                    "¿Atienden sin cita previa? Sí, medicina general en la sede San Isidro atiende por "
                    "orden de llegada de 07:00 a 12:00 horas, sujeto a disponibilidad de cupos.",
                ],
            ),
            (
                "Horarios y sedes",
                [
                    "¿Cuál es el horario de atención? Sede San Isidro: lunes a sábado de 07:00 a 21:00 "
                    "horas y emergencias 24/7. Sede Miraflores: lunes a viernes de 08:00 a 20:00 y sábados "
                    "de 08:00 a 14:00. Sede Surco: lunes a sábado de 07:30 a 20:00 horas.",
                    "¿Dónde quedan las sedes? San Isidro: Av. Javier Prado Este 1420. Miraflores: "
                    "Av. Larco 880. Surco: Av. Caminos del Inca 2350.",
                    "¿Hay estacionamiento? Las tres sedes cuentan con estacionamiento. Es gratuito por las "
                    "dos (2) primeras horas presentando el ticket validado en la Plataforma de Atención.",
                ],
            ),
            (
                "Resultados e historia clínica",
                [
                    "¿Cómo veo mis resultados? En la sección Resultados de la VidaSana App, con el mismo "
                    "usuario y contraseña del portal web. También se envía una notificación al correo "
                    "registrado cuando un resultado queda disponible.",
                    "¿Puedo pedir una copia de mi historia clínica? Sí. La solicitud se presenta en la "
                    "Plataforma de Atención al Usuario o al correo datospersonales@vidasana.pe. La primera "
                    "copia del año es gratuita; las siguientes cuestan S/ 25.00.",
                    "¿Cuánto demora la entrega de la historia clínica? Hasta veinte (20) días hábiles, "
                    "conforme al plazo del derecho de acceso.",
                ],
            ),
            (
                "Pagos y seguros",
                [
                    "¿Qué medios de pago aceptan? Efectivo, tarjetas Visa, Mastercard, American Express y "
                    "Diners, además de Yape, Plin y transferencia bancaria.",
                    "¿Puedo pagar en cuotas? Sí, en cuotas sin intereses hasta en seis (6) meses con "
                    "tarjetas de crédito de bancos afiliados, para consumos mayores a S/ 500.00.",
                    "¿Atienden pacientes sin seguro? Sí, bajo tarifa particular. También pueden acceder al "
                    "programa VidaSana Plus para obtener descuentos.",
                ],
            ),
            (
                "Otros",
                [
                    "¿Emiten certificados médicos? Sí, el certificado médico simple tiene un costo de "
                    "S/ 40.00 y se emite el mismo día de la consulta. El certificado con fines laborales o "
                    "de aptitud física cuesta S/ 90.00.",
                    "¿Cómo presento un reclamo? A través del Libro de Reclamaciones físico en cada sede o "
                    "del Libro de Reclamaciones virtual en vidasana.pe. El plazo de respuesta es de quince "
                    "(15) días hábiles.",
                    "¿Tienen atención en otros idiomas? La sede San Isidro cuenta con personal de atención "
                    "en inglés. Para lengua de señas peruana se debe solicitar el apoyo con cuarenta y "
                    "ocho (48) horas de anticipación.",
                ],
            ),
        ],
    },
}


# Especialidad, profesional, sede, días, horario, duración (min), tarifa particular (S/),
# tarifa VidaSana Plus (S/), requiere orden médica, acepta teleconsulta, cobertura de seguros
FILAS_CSV: list[list] = [
    ["Medicina General", "Dr. Ricardo Salas Peña", "San Isidro", "Lunes a Sábado", "07:00-21:00", 20, 90, 63, "No", "Sí", "Rímac, Pacífico, La Positiva, Mapfre, SIS"],
    ["Medicina General", "Dra. Carmen Ríos Ugarte", "Miraflores", "Lunes a Viernes", "08:00-20:00", 20, 90, 63, "No", "Sí", "Rímac, Pacífico, La Positiva, Mapfre, SIS"],
    ["Medicina General", "Dr. Aldo Fernández Cueva", "Surco", "Lunes a Sábado", "07:30-20:00", 20, 90, 63, "No", "Sí", "Rímac, Pacífico, La Positiva, Mapfre, SIS"],
    ["Pediatría", "Dra. Lucía Mendoza Vera", "San Isidro", "Lunes a Viernes", "09:00-18:00", 30, 150, 105, "No", "Sí", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Pediatría", "Dr. Manuel Ochoa Ruiz", "Surco", "Martes y Jueves", "14:00-20:00", 30, 150, 105, "No", "Sí", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Ginecología", "Dra. Patricia Valdez Soto", "Miraflores", "Lunes a Viernes", "08:00-16:00", 30, 180, 126, "No", "No", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Ginecología", "Dra. Elena Quispe Aliaga", "San Isidro", "Lunes, Miércoles y Viernes", "10:00-19:00", 30, 180, 126, "No", "No", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Cardiología", "Dr. Jorge Linares Bravo", "San Isidro", "Lunes a Viernes", "08:00-17:00", 40, 220, 154, "Sí", "Sí", "Rímac, Pacífico, Mapfre"],
    ["Cardiología", "Dra. Sofía Arellano Paz", "Surco", "Miércoles y Viernes", "09:00-15:00", 40, 220, 154, "Sí", "Sí", "Rímac, Pacífico, Mapfre"],
    ["Dermatología", "Dra. Andrea Cornejo Lazo", "Miraflores", "Lunes a Sábado", "09:00-19:00", 25, 200, 140, "No", "Sí", "Rímac, Pacífico, La Positiva"],
    ["Traumatología", "Dr. Héctor Paredes Solís", "San Isidro", "Lunes a Viernes", "07:00-15:00", 30, 210, 147, "Sí", "No", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Traumatología", "Dr. Iván Castillo Rojas", "Surco", "Martes, Jueves y Sábado", "08:00-14:00", 30, 210, 147, "Sí", "No", "Rímac, Pacífico, La Positiva, Mapfre"],
    ["Oftalmología", "Dra. Rosa Ninanya Huamán", "Miraflores", "Lunes a Viernes", "09:00-18:00", 25, 190, 133, "No", "No", "Rímac, Pacífico, Mapfre"],
    ["Otorrinolaringología", "Dr. Fabio Zegarra Mena", "San Isidro", "Martes y Jueves", "10:00-18:00", 25, 200, 140, "No", "No", "Rímac, Pacífico"],
    ["Endocrinología", "Dra. Mariana Torres Chávez", "San Isidro", "Lunes, Miércoles y Viernes", "08:00-14:00", 35, 230, 161, "Sí", "Sí", "Rímac, Pacífico, Mapfre"],
    ["Gastroenterología", "Dr. Álvaro Benites Loza", "Surco", "Lunes a Viernes", "08:00-16:00", 35, 240, 168, "Sí", "Sí", "Rímac, Pacífico, La Positiva"],
    ["Neurología", "Dra. Claudia Espinoza Vega", "San Isidro", "Martes, Jueves y Viernes", "09:00-17:00", 40, 260, 182, "Sí", "Sí", "Rímac, Pacífico"],
    ["Psicología", "Lic. Diego Ramírez Tapia", "Miraflores", "Lunes a Sábado", "08:00-20:00", 50, 130, 91, "No", "Sí", "Rímac, Pacífico, La Positiva"],
    ["Psiquiatría", "Dr. Enrique Bustamante Ríos", "San Isidro", "Miércoles y Sábado", "10:00-16:00", 45, 250, 175, "Sí", "Sí", "Rímac, Pacífico"],
    ["Nutrición", "Lic. Valeria Sánchez Núñez", "Surco", "Lunes a Viernes", "08:00-17:00", 40, 120, 84, "No", "Sí", "Pacífico, La Positiva"],
    ["Urología", "Dr. Óscar Delgado Ponce", "San Isidro", "Lunes y Miércoles", "14:00-20:00", 30, 230, 161, "Sí", "No", "Rímac, Pacífico, Mapfre"],
    ["Odontología", "Dra. Gabriela Ynga Portal", "Miraflores", "Lunes a Sábado", "09:00-19:00", 40, 110, 77, "No", "No", "Pacífico, La Positiva"],
    ["Reumatología", "Dr. Samuel Cárdenas Ita", "Surco", "Jueves", "09:00-15:00", 35, 240, 168, "Sí", "Sí", "Rímac, Pacífico"],
    ["Neumología", "Dra. Ximena Robles Farfán", "San Isidro", "Martes y Viernes", "08:00-14:00", 35, 235, 165, "Sí", "Sí", "Rímac, Pacífico, Mapfre"],
    ["Medicina Física y Rehabilitación", "Dr. Pablo Miranda Ávila", "Surco", "Lunes a Viernes", "07:30-15:30", 30, 170, 119, "Sí", "No", "Rímac, La Positiva, Mapfre"],
]

CABECERA_CSV = [
    "especialidad",
    "profesional",
    "sede",
    "dias_atencion",
    "horario",
    "duracion_min",
    "tarifa_particular_pen",
    "tarifa_vidasana_plus_pen",
    "requiere_orden_medica",
    "acepta_teleconsulta",
    "seguros_aceptados",
]


# --------------------------------------------------------------------------- #
# Generación
# --------------------------------------------------------------------------- #

def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloVidaSana",
            parent=base["Title"],
            fontSize=18,
            leading=23,
            spaceAfter=6,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloVidaSana",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor="#555555",
            spaceAfter=18,
        ),
        "seccion": ParagraphStyle(
            "SeccionVidaSana",
            parent=base["Heading2"],
            fontSize=13,
            leading=17,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "cuerpo": ParagraphStyle(
            "CuerpoVidaSana",
            parent=base["BodyText"],
            fontSize=10.5,
            leading=15.5,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "aviso": ParagraphStyle(
            "AvisoVidaSana",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=12,
            alignment=TA_JUSTIFY,
            textColor="#7A2E2E",
            backColor="#FBEDED",
            borderPadding=8,
            spaceAfter=18,
        ),
    }


def generar_pdf(nombre_archivo: str, definicion: dict, estilos: dict) -> Path:
    ruta = DIRECTORIO_DATOS / nombre_archivo
    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title=definicion["titulo"],
        author="Clínica VidaSana S.A.C.",
    )

    elementos = [
        Paragraph(definicion["titulo"], estilos["titulo"]),
        Paragraph(definicion["subtitulo"], estilos["subtitulo"]),
        Paragraph(AVISO_FICCION, estilos["aviso"]),
    ]
    for encabezado, parrafos in definicion["secciones"]:
        elementos.append(Paragraph(encabezado, estilos["seccion"]))
        for parrafo in parrafos:
            elementos.append(Paragraph(parrafo, estilos["cuerpo"]))
    elementos.append(Spacer(1, 12))

    documento.build(elementos)
    return ruta


def generar_csv() -> Path:
    ruta = DIRECTORIO_DATOS / "especialidades_y_tarifas_vidasana.csv"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(CABECERA_CSV)
        escritor.writerows(FILAS_CSV)
    return ruta


def main() -> None:
    DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)
    estilos = _estilos()

    for nombre_archivo, definicion in DOCUMENTOS.items():
        ruta = generar_pdf(nombre_archivo, definicion, estilos)
        print(f"PDF generado: {ruta.relative_to(RAIZ)}")

    ruta_csv = generar_csv()
    print(f"CSV generado: {ruta_csv.relative_to(RAIZ)} ({len(FILAS_CSV)} filas)")


if __name__ == "__main__":
    main()
