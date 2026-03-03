import streamlit as st
from exa_py import Exa
from groq import Groq
import re

# 1. Setup the UI
st.set_page_config(page_title="Music Breakdown Tool", page_icon="🎵")
st.title("🎵 Spanish & Universal Music Tool")
st.write("Enter a song title and artist to get the key, tempo, time signature, and measure-by-measure chords.")

# 2. Connect the Keys 
try:
    exa = Exa(api_key=st.secrets["EXA_API_KEY"])
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("API keys not found. Please check your Streamlit Secrets.")
    st.stop()

# 3. The Search Bar
song_input = st.text_input("Song Title & Artist", placeholder="e.g., Vivir Mi Vida - Marc Anthony")

# 4. The "Analyze" Button Logic
if st.button("Analyze Song"):
    if song_input:
        with st.spinner(f"Scouring music sources for '{song_input}'..."):
            try:
                # --- A. The Search Phase (Exa) ---
                search_query = f"{song_input} chords"
                
                # PRIORITY SEARCH: Target the 4 specific sites you requested
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    num_results=5,
                    include_domains=["ultimate-guitar.com", "lacuerda.net", "guitarsongs.club", "cifraclub.com", "cifraclub.com.br"],
                    text=True
                )
                
                # FALLBACK SEARCH: If the priority sites have nothing, search anywhere similar
                if not search_results.results:
                    search_results = exa.search_and_contents(
                        search_query,
                        type="neural",
                        num_results=5,
                        text=True
                    )
                
                # Combine the raw text
                context_text = ""
                for result in search_results.results:
                    context_text += f"Source URL: {result.url}\nContent: {result.text}\n\n"
                    
                # --- B. The Brain Phase (Groq) ---
                prompt = f"""
                You are a professional Musicologist. Extract high-accuracy musical data for '{song_input}' using ONLY the provided text.
                
                REQUIRED DATA POINTS (Format your output with these exact headers):
                1. **Key:** 2. **Tempo (BPM):** Look carefully for terms like "tempo", "BPM", "beats per minute", or metronome marks. 
                3. **Time Signature:** Look for 4/4, 3/4, 6/8, etc. 
                4. **Song Structure:** List the sections found (e.g., Intro, Verse, Pre-Chorus, Chorus, Bridge).
                5. **Chord Progression:** Provide a clear Markdown table mapping the chords to each specific section.
                
                STRICT RULES:
                1. DO NOT GUESS. If a specific data point (like BPM or Time Signature) isn't explicitly found in the text, say "Unknown".
                2. DOUBLE CHECK: Double check data and cross reference to ensure maximum accuracy.
                3. BILINGUAL SUPPORT: Translate Spanish/Portuguese notes (Do, Re, Mi) to English (C, D, E).
                
                ACCURACY ESTIMATE:
                At the end, provide an "Accuracy Confidence Score" from 0-100%. 
                Explain WHY you gave that score, and mention which site provided the best data.

                TEXT TO ANALYZE:
                {context_text}
                """
                
                # Using the heavy-duty model for deep reasoning
                chat_completion = groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1, 
                )
                
                # --- C. Display the Result ---
                st.success("Analysis Complete!")
                response_content = chat_completion.choices[0].message.content
                st.markdown(response_content)

                # --- D. Accuracy Visualization ---
                match = re.search(r"(\d+)%", response_content)
                if match:
                    score = int(match.group(1))
                    st.write(f"**Tool Confidence Score: {score}%**")
                    st.progress(score / 100.0) 

            except Exception as e:
                st.error(f"Looks like we hit a snag: {e}")
    else:
        st.warning("Please type a song name first!")