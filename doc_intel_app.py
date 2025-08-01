import streamlit as st
# import ollama
import re
from statistics import median
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

# # Set the model name for our LLMs
# GEMINI_MODEL = "gemini-1.5-flash"
# # GEMINI_MODEL = "models/gemini-pro"
# # Store the API key in a variable.
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# # ✅  Initialize the model
# llm = ChatGoogleGenerativeAI(google_api_key=GEMINI_API_KEY, model=GEMINI_MODEL, temperature=0.3)


# ------------------------------------------------------------
# 📌 EF Extraction helpers
# ------------------------------------------------------------
PATTERNS = {
    'summary': r'\b(Summary|Conclusion|IMPRESSION|FINDING)\b',
    'threeD': r'3D EF',
    'biplane': r'Biplane',
    'sp4': r'MOD-sp4',
    'sp2': r'MOD-sp2',
    'ef': r'(ejection fraction|LVEF|LLVEF|lv ef|3D EF|EF )'
}

def get_matches(pattern, text, window=50):
    matches = []
    for m in re.finditer(pattern, text, re.IGNORECASE):
        start = max(m.start() - window, 0)
        end = m.end() + window
        matches.append(text[start:end])
    return matches

def extract_ef_from_context(contexts):
    results = []
    for ctx in contexts:
        found = re.findall(r'\b\d{2,3}\s*%+', ctx)
        for val in found:
            val_clean = re.findall(r'\d{2,3}', val)
            results.extend(val_clean)
    return results

def extract_ef_from_text(text):
    contexts = []
    results = []
    for key in ['summary', 'threeD', 'biplane', 'sp4', 'sp2', 'ef']:
        ctx = get_matches(PATTERNS[key], text, window=50 if key in ['summary', 'ef'] else 10)
        if ctx:
            efs = extract_ef_from_context(ctx)
            if efs:
                contexts = ctx
                results = efs
                break
    if results:
        results = [int(x) for x in results]
        ef_median = median(results)
        return f"✅ EF values found: {results}\n✅ Median EF: {ef_median}"
    else:
        return "⚠️ No EF values found."

# ------------------------------------------------------------
# 📌 Mistral Abnormality extractor via Ollama
# ------------------------------------------------------------
# def extract_abnormalities(narrative):
#     prompt = f"""
# Given the following diagnostic report, identify the MAJOR abnormalities noted. Categorize the abnormalities as needed.

# Comment:
# \"\"\"{narrative}\"\"\"
# """
#     try:
#         response = ollama.chat(
#             model='mistral',
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response['message']['content'].strip()
#     except Exception as e:
#         return f"❌ Error: {e}"


# Load Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")

def extract_abnormalities(narrative):
    prompt = f"""
Given the following diagnostic report, identify the MAJOR abnormalities noted. Categorize the abnormalities as needed.

Comment:
\"\"\"{narrative}\"\"\"
"""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Error: {e}"

# ------------------------------------------------------------
# 📌 Combined
# ------------------------------------------------------------
def analyze_report(narrative):
    abnormalities = extract_abnormalities(narrative)
    ef_output = extract_ef_from_text(narrative)
    return abnormalities, ef_output

# ------------------------------------------------------------
# ✅ Streamlit App
# ------------------------------------------------------------
st.set_page_config(page_title="EF & Abnormalities Extractor", layout="centered")
st.title("🫀 Document Intelligence:  Ejection Fraction & Abnormalities Diagnostic Extractor")

st.markdown("""
Paste any diagnostic **Narrative** below and get:

- ✅ Major abnormalities 
- ✅ Ejection Fraction values & median 

Powered by CALIBER360 Healthcare AI
""")

EXAMPLE_TEXT = """Health System Alpha Medical Center;X Medical Drive;Medville, CA xxxxx;(xxx)xxx-xxxx;Transthoracic Echocardiogram;Name: Patient X #: 123456;DOB: xx/xx/19xx;Age: 92 years;Gender: F;Study date: xx/xx/2xxx;Accession #: xxxxxxxxx;Account #:xxxxxxxx;Height: 63 in;Weight: 117.7 lb;BSA: 1.54 m squared;Location: Inpatient;Indications: Myocardial Infarction.;Reading Physician: MyDoc1;Ordering Physician:  MyDoc2, M.D.;Cardiac Sonographer:  MyDoc3;PROCEDURE: This was a routine study. The transthoracic approach;was used. The study included complete 2D imaging, M-mode,;complete spectral Doppler, and color Doppler.;LEFT VENTRICLE: Size was normal. Systolic function was normal.;Ejection fraction was estimated in the range of 50 % to 55 %.;There were no regional wall motion abnormalities. Wall thickness;was mildly to moderately increased.;RIGHT VENTRICLE: The size was normal. Systolic function was;normal. DOPPLER: Estimated peak pressure was 33 mmHg.;LEFT ATRIUM: The atrium was mildly dilated.;ATRIAL SEPTUM: No defect or patent foramen ovale was identified;by color Doppler.;RIGHT ATRIUM: The atrium was dilated.;MITRAL VALVE: Valve structure was normal. There was normal;leaflet separation. DOPPLER: The transmitral velocity was within;the normal range. There was no evidence for stenosis. There was;moderate regurgitation.;AORTIC VALVE: The valve was trileaflet. Leaflets exhibited;mildly increased thickness and normal cuspal separation.;DOPPLER: Transaortic velocity was within the normal range. There;was no evidence for stenosis. There was trace regurgitation.;TRICUSPID VALVE: The valve structure was normal. There was;normal leaflet separation. DOPPLER: There was no evidence for;stenosis. There was moderate regurgitation.;PULMONIC VALVE: Leaflets exhibited normal thickness, no;calcification, and normal cuspal separation. DOPPLER: There was;trace regurgitation.;AORTA: The root exhibited normal size.;SYSTEMIC VEINS: IVC: The inferior vena cava was dilated.;Inspiratory collapse was less than 50%.;PERICARDIUM: There was no pericardial effusion. The pericardium;was normal in appearance.;SYSTEM MEASUREMENT TABLES;2D mode;LVIDd (2D): 3.51 cm;LVIDs (2D): 2.59 cm;LVPWd (2D): 1.47 cm;M mode;AoR Diam (MM): 3.3 cm;AoR Diam; Mean (MM): 3.3 cm;AV Cusp Sep (MM): 1.8 cm;LA Dimension (MM): 4.3 cm;Unspecified Scan Mode;MV Peak E Vel; Antegrade Flow: 86.8 cm/s;MVA (PHT): 1.85 cm2;Mean Grad; Antegrade Flow: 1 mm[Hg];PHT: 114 ms;PHT Peak Vel;: 82.5 cm/s;Peak Grad; Mean; Antegrade Flow: 2 mm[Hg];VTI; Mean; Antegrade Flow: 27.8 cm;Peak Grad; Mean; Antegrade Flow: 2 mm[Hg];RVSP: 37 mm[Hg];Vmax; Regurgitant Flow: 229 cm/s;SUMMARY:;-  Left ventricle:;-  Systolic function was normal. Ejection fraction was estimated;in the range of 50 % to 55 %.;-  There were no regional wall motion abnormalities.;-  Wall thickness was mildly to moderately increased.;-  Right ventricle:;-  Estimated peak pressure was 33 mmHg.;-  Left atrium:;-  The atrium was mildly dilated.;-  Right atrium:;-  The atrium was dilated.;-  Mitral valve:;-  There was moderate regurgitation.;-  Tricuspid valve:;-  There was moderate regurgitation.;-  IVC, hepatic veins:;-  The inferior vena cava was dilated.;-  Inspiratory collapse was less than 50%.;Prepared and signed by;MyDoc1, M.D.;Signed xx/xx/xxxx 18:11:12"""

# # Text area for input
# narrative_input = st.text_area(
#     "Paste Your Echocardiogram Narrative Here (INPUT)",
#     value=EXAMPLE_TEXT,
#     height=300
# )

EXAMPLE_ABNORMALITIES = """The major abnormalities noted in the echocardiogram report for Patient X are:
Valvular Abnormalities:

Moderate mitral regurgitation: Significant backflow of blood from the left ventricle to the left atrium.
Moderate tricuspid regurgitation: Significant backflow of blood from the right ventricle to the right atrium.
Atrial Abnormalities:

Right atrial dilation: Enlargement of the right atrium, suggesting possible underlying right-sided heart strain or dysfunction.
Mild left atrial dilation: Slight enlargement of the left atrium, which may be related to the mitral regurgitation.
Venous Abnormalities:

Dilated inferior vena cava (IVC) with reduced inspiratory collapse (<50%): This suggests increased central venous pressure, potentially indicating right heart failure or volume overload.
Other Abnormalities:

Mildly to moderately increased left ventricular wall thickness: While systolic function is normal, this suggests possible hypertrophy, a compensatory mechanism often seen in response to increased afterload (e.g., hypertension). Further investigation is needed to determine the cause.
Less Significant Abnormalities (considered minor in the context of the others):

Mildly increased aortic valve thickness: This is noted as mild and doesn't appear to cause hemodynamic compromise (no significant stenosis or regurgitation).
Trace aortic and pulmonic regurgitation: Minimal backflow, generally considered insignificant unless it worsens.
The combination of moderate mitral and tricuspid regurgitation, right atrial dilation, and dilated IVC strongly suggests the presence of right-sided heart failure. The mildly to moderately increased left ventricular wall thickness warrants further investigation to determine the underlying cause."""

EXAMPLE_EF = "✅ EF values found: [50, 55]\n✅ Median EF: 52.5"

# Analyze button
# if st.button("🔎 Analyze Narrative"):
#     with st.spinner("Analyzing..."):
#         abnormalities, ef_output = analyze_report(narrative_input)
#     st.subheader("🔍 Key Abnormalities (OUTPUT #1)")
#     st.code(abnormalities, language='markdown')
#     st.subheader("📏 Ejection Fraction (EF) Distinct Records & Median (OUTPUT #2)")
#     st.code(ef_output, language='markdown')
# Automatically analyze on load
# with st.spinner("Analyzing..."):
#     abnormalities, ef_output = analyze_report(narrative_input)

# # Display results immediately
# st.subheader("🔍 Key Abnormalities (OUTPUT #1)")
# st.code(EXAMPLE_ABNORMALITIES, language='markdown')

# st.subheader("📏 Ejection Fraction (EF) Distinct Records & Median (OUTPUT #2)")
# st.code(EXAMPLE_EF, language='markdown')
# Text area for input
# Text area for input
narrative_input = st.text_area(
    "Paste Your Echocardiogram Narrative Here (INPUT)",
    value=EXAMPLE_TEXT,
    height=300
)

# Always show the button
analyze_clicked = st.button("🔎 Analyze Narrative")

st.markdown("<hr style='margin-top: 25px; margin-bottom: 25px;'>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; font-size: 22px; font-weight: bold; color: #031d44; margin-bottom: 20px;'>
📄 Output of CALIBER360 Document Intelligence
</div>
""", unsafe_allow_html=True)


# Check if input is the same as example
is_default_input = narrative_input.strip() == EXAMPLE_TEXT.strip()

# Show output
if is_default_input and not analyze_clicked:
    # Show default output immediately (on load)
    # st.subheader("🔍 Key Abnormalities (OUTPUT #1)")
    # st.code(EXAMPLE_ABNORMALITIES, language='markdown')

    # st.subheader("📏 Ejection Fraction (EF) Distinct Records & Median (OUTPUT #2)")
    # st.code(EXAMPLE_EF, language='markdown')
    st.markdown("""
<div style="background-color:#f0f8ff; border-left:5px solid #1E90FF; padding:20px; border-radius:5px;">
<h4>🔍 Key Abnormalities</h4>
<pre style="white-space: pre-wrap;">{}</pre>
</div>
""".format(EXAMPLE_ABNORMALITIES), unsafe_allow_html=True)

    st.markdown("""
<div style="background-color:#e8fff5; border-left:5px solid #2E8B57; padding:20px; border-radius:5px; margin-top: 20px;">
<h4>📏 Ejection Fraction (EF) Distinct Records & Median</h4>
<pre style="white-space: pre-wrap;">{}</pre>
</div>
""".format(EXAMPLE_EF), unsafe_allow_html=True)

elif analyze_clicked:
    with st.spinner("Analyzing..."):
        abnormalities, ef_output = analyze_report(narrative_input)

    # st.subheader("🔍 Key Abnormalities")
    # st.code(abnormalities, language='markdown')

    # st.subheader("📏 Ejection Fraction (EF) Distinct Records & Median")
    # st.code(ef_output, language='markdown')
    st.markdown("""
<div style="background-color:#f0f8ff; border-left:5px solid #1E90FF; padding:20px; border-radius:5px;">
<h4>🔍 Key Abnormalities</h4>
<pre style="white-space: pre-wrap;">{}</pre>
</div>
""".format(abnormalities), unsafe_allow_html=True)

    st.markdown("""
<div style="background-color:#e8fff5; border-left:5px solid #2E8B57; padding:20px; border-radius:5px; margin-top: 20px;">
<h4>📏 Ejection Fraction (EF) Distinct Records & Median</h4>
<pre style="white-space: pre-wrap;">{}</pre>
</div>
""".format(ef_output), unsafe_allow_html=True)

