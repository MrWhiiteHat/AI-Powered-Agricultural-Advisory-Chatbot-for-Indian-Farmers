import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_report():
    doc = docx.Document()
    
    # Title
    title = doc.add_heading('KrishiMitra (कृषि मित्र)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph('AI-Powered Agricultural Advisory Chatbot for Indian Farmers')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph('\n')
    
    # Overview
    doc.add_heading('1. Project Overview', level=1)
    doc.add_paragraph('KrishiMitra is a highly resilient AI chatbot designed to provide real-time, localized agricultural advice to small-scale farmers. Often lacking timely information, farmers face preventable crop losses. KrishiMitra bridges this gap by delivering exact insights natively in vernacular languages via WhatsApp and a dedicated isolated Web Application.')
    doc.add_paragraph('The chatbot utilizes advanced Artificial Intelligence capabilities including Computer Vision for disease detection, Speech-to-Text for vernacular voice interactions, and Retrieval-Augmented Generation (RAG) backed by external real-time datastreams like OpenWeatherMap and Agmarknet.')

    # Features
    doc.add_heading('2. Key Features', level=1)
    features = [
        "Crop Disease Detection: Users upload a photo of a sick plant leaf. A custom-trained deep learning Convolutional Neural Network (CNN) analyzes the image, identifies the exact disease securely, and prescribes a precise chemical/organic treatment plan.",
        "Voice & Multilingual Interaction: Farmers may send raw voice messages in Hindi or English (via WhatsApp). The system leverages OpenAI Whisper for asynchronous audio transcription, and Gemini translates LLM replies back to the user's preferred language seamlessly.",
        "Hyper-Local Weather Advisory: Accesses live meteorological telemetry via the OpenWeatherMap REST API and correlates it with registered crops to produce deterministic irrigation recommendations.",
        "Live Mandi Prices: Fetches current market pricing to maximize agricultural profitability.",
        "Government Schemes (RAG): Queries an integrated JSON Knowledge Base using vector simulation to match farmers with subsidies they are intrinsically eligible for.",
        "Graceful Fallback & Degradation Architecture: Deep resilience mechanisms ensure that if heavy Machine Learning models (e.g., TensorFlow) crash or lack physical server RAM, the system defaults to mocked configurations to guarantee 100% online availability for WhatsApp responses."
    ]
    for feat in features:
        doc.add_paragraph(feat, style='List Bullet')

    # Architecture & Technology Stack
    doc.add_heading('3. System Architecture & Tech Stack', level=1)
    doc.add_paragraph('The system is built on an Asynchronous Pipeline optimized for maximum parallel processing on minimal hardware. The complete layout of technologies utilized is detailed below:')
    
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Component'
    hdr_cells[1].text = 'Technology'
    hdr_cells[2].text = 'Purpose'
    for cell in hdr_cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                
    tech_data = [
        ('Backend API', 'FastAPI (Python)', 'High-performance, async web framework handling Twilio routing.'),
        ('LLM Inference Engine', 'Google Gemini 2.5 Flash', 'Intent classification, empathy extraction, & multi-lingual orchestration.'),
        ('Computer Vision', 'TensorFlow MobileNetV2', 'Deep learning CNN trained on PlantVillage (54,000+ datasets) for disease anomaly detection.'),
        ('Speech-to-Text', 'OpenAI Whisper', 'Native multi-accent verbal translation.'),
        ('Active Database', 'MongoDB (Motor / Async)', 'NoSQL storage for farmer profiling and chronological memory retention.'),
        ('Frontend Telemetry', 'Twilio API', 'Cryptographic abstraction layer connecting Python to WhatsApp.')
    ]
    
    for item in tech_data:
        row_cells = table.add_row().cells
        row_cells[0].text = item[0]
        row_cells[1].text = item[1]
        row_cells[2].text = item[2]
        
    doc.add_paragraph('\n')

    # Data Workflow
    doc.add_heading('4. Interaction Workflow Pipeline', level=1)
    doc.add_paragraph("The interaction lifecycle dictates how data autonomously travels across the server:")
    pipeline = [
        "1. Ingestion: WhatsApp messages (Text/Voice/Image) ping the local FastAPI server through secure Ngrok tunneling via the Twilio Sandbox.",
        "2. Interception: Media boundaries are decoupled. Voice is converted identically to text.",
        "3. LLM Intent Router: Google GenAI inspects the isolated intent (i.e. 'weather request' vs. 'general chat').",
        "4. Telemetry Scraping: The specific endpoint calls related APIs (e.g. WeatherService).",
        "5. Prompt Augmentation: Environmental context combined with the raw text is fed to LLM to create humanized text.",
        "6. Outbound Dispatch: Constructed text output successfully dispatches back out to Twilio, fulfilling the asynchronous communication circuit."
    ]
    for step in pipeline:
        doc.add_paragraph(step)

    # Conclusion
    doc.add_heading('5. Future Directions', level=1)
    doc.add_paragraph('KrishiMitra represents an autonomous shift in agricultural extension services. By decentralizing and translating core farming mechanics directly into the tools the farmer already utilizes (WhatsApp), it prevents dependency on external physical consultants and directly minimizes crop morbidity.')

    # Save
    doc.save(r'd:\AI CLG Project\KrishiMitra_Complete_Documentation.docx')
    print("DocX Report Generated Successfully.")

if __name__ == '__main__':
    create_report()
