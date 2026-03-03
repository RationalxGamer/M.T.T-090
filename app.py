import streamlit as st
from exa_py import Exa
from groq import Groq
import google.generativeai as genai
import re

# 1. Setup the UI
st.set_page_config(page_title="Music Breakdown Tool", page_icon="🎵")
st.title("🎵 Spanish & Universal Music Tool")
st.write("Enter a song title and artist to get the key, tempo, time signature, and measure-by-measure chords.")

# 2. Connect the Keys
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
        with st.spinner(f"Searching, Drafting, and Verifying '{song_input}'..."):
            try:
                # --- PHASE 1: The Scout (Exa) ---
                search_query = f"{song_input} chords"
                
                # LaCuerda removed. 
                priority_domains = [
                    "ultimate-guitar.com", 
                    "guitarsongs.club", 
                    "cifraclub.com", 
                    "cifraclub.com.br",
                    "acordesweb.com",
                    "acordesdcanciones.com"
                ]
                
                # Bumping num_results to 10 forces Exa to pull from multiple sites on the list
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    num_results=10, 
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
                Your assistant has drafted a chord breakdown for '{song_input}'. You must verify it against the raw source text.
                
                RAW SOURCE TEXT:
                {context_text}
                
                ASSISTANT'S DRAFT:
                {groq_draft}
                
                YOUR TASKS:
                1. STRICT IDENTITY CHECK: Your absolute priority is the requested song: '{song_input}'. Do not assume, interpret, or "fix" the user's search. If the exact song by the exact artist is not explicitly found in the text, output ONLY: "Error: No accurate data found for this exact song."
                2. CROSS-REFERENCE MANDATE: You have data from multiple sites. You must actively compare them. Do not rely on just the first source. If sources disagree, favor the one with the most structured tablature.
                3. NO GUESSWORK: If a specific detail (like BPM or Time Signature) is missing across ALL sources, explicitly state "Unknown". Do not calculate or guess.
                4. LASER FOCUS: Ignore any sidebars, "related songs", or "top tracks" mentioned in the text.
                5. BILINGUAL SUPPORT: Translate Spanish/Portuguese notes (Do, Re, Mi) to English standard (C, D, E).
                6. FORMAT: Output final data with these exact headers: **Key:**, **Tempo (BPM):**, **Time Signature:**, and a clean Markdown table for the **Chord Progression**.
                7. CONFIDENCE SCORE: End with an "Accuracy Confidence Score" (0-100%) explaining your cross-referencing process and noting if any sources conflicted.
                """
                
                # Using the stable, high-limit Flash model
                gemini_model = genai.GenerativeModel('gemini-3-flash-preview')
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