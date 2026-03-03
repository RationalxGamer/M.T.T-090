import streamlit as st
from exa_py import Exa
from groq import Groq
import re

# 1. Setup the UI
st.set_page_config(page_title="Music Breakdown Tool", page_icon="🎵")
st.title("🎵 Spanish & Universal Music Tool")
st.write("Enter a song title and artist to get the key, tempo, and measure-by-measure chords.")

# 2. Connect the Keys (Securely pulling from your Streamlit Vault)
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
        with st.spinner(f"Thoroughly scouring verified music sources for '{song_input}'..."):
            try:
                # --- A. The Search Phase (Exa) ---
                # Strictly searching your 4 requested verified sources
                search_query = f"{song_input} \"official\" OR \"verified\" chords site:ultimate-guitar.com OR site:lacuerda.net OR site:guitarsongs.club OR site:cifraclub.com"
                
                search_results = exa.search_and_contents(
                    search_query,
                    type="neural",
                    num_results=5, # Deep search across 5 pages
                    text=True
                )
                
                # Combine the raw text, including the URL so the AI knows where it came from
                context_text = ""
                for result in search_results.results:
                    context_text += f"Source URL: {result.url}\nContent: {result.text}\n\n"
                    
                # --- B. The Brain Phase (Groq) ---
                prompt = f"""
                You are a professional Musicologist. Extract high-accuracy musical data for '{song_input}' using ONLY the provided text.
                
                STRICT RULES:
                1. DO NOT GUESS. If BPM or Key isn't explicitly found, say "Unknown".
                2. CROSS-REFERENCE: You have data from up to 5 sources. Compare them to find the most accurate chord progression.
                3. FAVOR TABLATURE: Look for chord symbols placed over lyrics or in structured grids.
                4. BILINGUAL SUPPORT: Translate Spanish/Portuguese notes (Do, Re, Mi) to English (C, D, E).
                5. TABLE FORMAT: Provide the chord progression in a clear Markdown table by section (Intro, Verse, Chorus).
                
                ACCURACY ESTIMATE:
                At the end, provide an "Accuracy Confidence Score" from 0-100%. 
                - 90%+: Found matching, high-quality data across multiple sites.
                - 50-70%: Data found but there are discrepancies between sites.
                - Below 50%: Data was messy, missing, or highly speculative.
                Explain WHY you gave that score, and mention which site provided the best data.

                TEXT TO ANALYZE:
                {context_text}
                """
                
                # Upgraded to the massive 70B model for deep reasoning
                chat_completion = groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1, # Highly factual, low creativity
                )
                
                # --- C. Display the Result ---
                st.success("Analysis Complete!")
                response_content = chat_completion.choices[0].message.content
                st.markdown(response_content)

                # --- D. Accuracy Visualization ---
                # Looks for the % number in the AI's message and makes a visual bar
                match = re.search(r"(\d+)%", response_content)
                if match:
                    score = int(match.group(1))
                    st.write(f"**Tool Confidence Score: {score}%**")
                    st.progress(score / 100.0) 

            except Exception as e:
                st.error(f"Looks like we hit a snag: {e}")
    else:
        st.warning("Please type a song name first!")