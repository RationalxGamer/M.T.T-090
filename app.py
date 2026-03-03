import streamlit as st
from exa_py import Exa
from groq import Groq
import google.generativeai as genai
import re

# 1. Setup the UI
st.set_page_config(page_title="Music Breakdown Tool", page_icon="🎵")
st.title("🎵 Spanish & Universal Music Tool")
st.write("Enter a song title and artist to get the key, tempo, time signature, and measure-by-measure chords.")

# 2. Connect the Keys (The Assembly Line)
try:
    exa = Exa(api_key=st.secrets["EXA_API_KEY"])
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API keys not found. Please check your Streamlit Secrets.")
    st.stop()

# 3. The Search Bar
song_input = st.text_input("Song Title & Artist", placeholder="e.g., Vivir Mi Vida - Marc Anthony")

# 4. The "Analyze" Button Logic
if st.button("Analyze Song"):
    if song_input:
        # Updated spinner text to reflect the new heavy-duty process
        with st.spinner(f"Searching, Drafting, and Verifying '{song_input}'... (This takes a moment)"):
            try:
                # --- PHASE 1: The Scout (Exa) ---
                search_query = f"{song_input} chords"
                
                # Expanded Priority List
                priority_domains = [
                    "ultimate-guitar.com", 
                    "lacuerda.net", 
                    "guitarsongs.club", 
                    "cifraclub.com", 
                    "cifraclub.com.br",
                    "acordesweb.com",
                    "acordesdcanciones.com"
                ]
                
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    num_results=5,
                    include_domains=priority_domains,
                    text=True
                )
                
                # Fallback Search
                if not search_results.results:
                    search_results = exa.search_and_contents(
                        search_query,
                        type="neural",
                        num_results=5,
                        text=True
                    )
                
                context_text = ""
                for result in search_results.results:
                    context_text += f"Source URL: {result.url}\nContent: {result.text}\n\n"
                    
                # --- PHASE 2: The Worker Draft (Groq) ---
                groq_prompt = f"""
                You are a Music Data Extractor. Extract the raw musical data for '{song_input}' from the text below.
                Find the Key, Tempo (BPM), Time Signature, and map the chords to the song sections.
                Do not worry about perfect formatting, just get the raw data down accurately.
                
                TEXT:
                {context_text}
                """
                
                groq_draft = groq.chat.completions.create(
                    messages=[{"role": "user", "content": groq_prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1, 
                ).choices[0].message.content

                # --- PHASE 3: The Supervisor (Gemini) ---
                gemini_prompt = f"""
                You are the Master Musicologist Supervisor. 
                Your assistant has drafted a chord breakdown, but you must verify it for flawless accuracy against the raw source text.
                
                RAW SOURCE TEXT:
                {context_text}
                
                ASSISTANT'S DRAFT:
                {groq_draft}
                
                YOUR TASKS:
                1. VERIFY AND FIX: Cross-reference the draft with the raw text. Fix any hallucinations (especially incorrect generic Latin chord loops).
                2. FILL IN THE BLANKS: If the draft missed the BPM, Time Signature, or Key, search the raw text deeply to find it. If it truly does not exist in the text, explicitly state "Unknown".
                3. BILINGUAL SUPPORT: Ensure all Spanish/Portuguese notes (Do, Re, Mi) are translated to English standard (C, D, E).
                4. FORMAT: Output the final data clearly with these exact headers: **Key:**, **Tempo (BPM):**, **Time Signature:**, and a clean Markdown table for the **Chord Progression** by section.
                5. CONFIDENCE SCORE: End with an "Accuracy Confidence Score" (0-100%) explaining why you gave that score and which specific URL provided the best data.
                """
                
                gemini_model = genai.GenerativeModel('gemini-3-flash')
                final_response = gemini_model.generate_content(gemini_prompt).text
                
                # --- Display the Final Verified Result ---
                st.success("Analysis and Verification Complete!")
                st.markdown(final_response)

                # Accuracy Visualization
                match = re.search(r"(\d+)%", final_response)
                if match:
                    score = int(match.group(1))
                    st.write(f"**Supervisor Confidence Score: {score}%**")
                    st.progress(score / 100.0) 

            except Exception as e:
                st.error(f"Looks like we hit a snag: {e}")
    else:
        st.warning("Please type a song name first!")