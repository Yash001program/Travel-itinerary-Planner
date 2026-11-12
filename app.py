from datetime import date, timedelta
import streamlit as st

from llm_service import (
    generate_itinerary,
    recommend_destinations,
    regenerate_day_or_slot,
)
from pdf_generator import generate_itinerary_pdf
from storage import (
    convert_currency,
    delete_trip,
    init_trip_store,
    save_trip,
)

# ---------------------------------------------------------------------------
# PAGE CONFIG & MODERN WANDERLUST CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Personalized Travel Itinerary Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

WANDERLUST_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .hero-banner {
        background: linear-gradient(120deg, #0f4c5c 0%, #1b6b7d 55%, #e36414 100%);
        padding: 1.75rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px rgba(15, 76, 92, 0.18);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-banner p {
        margin: 0.4rem 0 0 0;
        opacity: 0.92;
        font-size: 0.98rem;
    }

    .dest-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 5px solid #0f4c5c;
        border-radius: 14px;
        padding: 1.25rem;
        height: 100%;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }
    .tag-pill {
        display: inline-block;
        background: #f0f9ff;
        color: #0f4c5c;
        border: 1px solid #bae6fd;
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        font-size: 0.76rem;
        font-weight: 600;
        margin: 0.15rem 0.2rem 0.15rem 0;
    }

    .cluster-header {
        background: linear-gradient(90deg, #f0fdfa 0%, #fff7ed 100%);
        border-left: 5px solid #e36414;
        padding: 0.9rem 1.2rem;
        border-radius: 10px;
        margin: 1rem 0 0.75rem 0;
    }
    .slot-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }
    .slot-badge {
        background: #0f4c5c;
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        margin-right: 0.5rem;
    }
    .cost-pill {
        float: right;
        background: #fef3c7;
        color: #92400e;
        font-weight: 700;
        font-size: 0.82rem;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
    }
</style>
"""
st.markdown(WANDERLUST_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
init_trip_store(st.session_state)
if "active_itinerary" not in st.session_state:
    st.session_state.active_itinerary = None
if "recommended_cities" not in st.session_state:
    st.session_state.recommended_cities = []
if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = ""

# ---------------------------------------------------------------------------
# SIDEBAR: EPIC 3 CONFIGURATION & TRIP PREFERENCES
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔐 AI Engine Configuration")
    demo_mode = st.toggle(
        "Demo Mode (Zero API Key Required)",
        value=True,
        help="Uses built-in geographically clustered itineraries & recommender. Disable to use live Gemini or Groq.",
    )
    provider = st.selectbox("LLM Provider", ["Google Gemini", "Groq"], disabled=demo_mode)
    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        placeholder="Paste API key...",
        disabled=demo_mode,
    )

    st.divider()
    st.markdown("### 🧳 Trip Preferences")

    destination_input = st.text_input(
        "Destination (Leave blank for AI Discovery)",
        value=st.session_state.selected_destination,
        placeholder="e.g., Kyoto, Udaipur, Phuket, or leave empty",
    )
    vibe = st.selectbox(
        "Open-Ended Travel Vibe",
        ["Cultural", "Beach", "Mountains", "Urban"],
        index=0,
    )
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        duration = st.number_input("Duration (Days)", min_value=1, max_value=14, value=3)
    with col_d2:
        start_date = st.date_input("Start Date", value=date.today() + timedelta(days=14))

    budget_level = st.select_slider(
        "Budget Tier",
        options=["Budget", "Moderate", "Luxury"],
        value="Moderate",
    )
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        party = st.selectbox("Travel Party", ["Solo", "Couple", "Family", "Friends"], index=1)
    with col_p2:
        pace = st.selectbox("Travel Pace", ["Relaxed", "Moderate", "Fast-Paced"], index=1)

    interests = st.multiselect(
        "Core Interests",
        ["Food", "Adventure", "History", "Nightlife"],
        default=["Food", "History"],
    )

    preferences = {
        "destination": destination_input.strip(),
        "vibe": vibe,
        "duration": int(duration),
        "start_date": str(start_date),
        "budget": budget_level,
        "party": party,
        "pace": pace,
        "interests": interests or ["Food", "History"],
    }

    st.markdown("---")
    generate_btn = st.button("✨ Generate Optimized Itinerary", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-banner">
        <h1>🧭 Personalized Travel Itinerary Planner</h1>
        <p>Geographically clustered day plans, multi-currency budget tracking, surgical slot swaps & offline PDF guides.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Trigger full generation from sidebar button
if generate_btn:
    if not demo_mode and not api_key:
        st.error("Please enter an API key or enable **Demo Mode** in the sidebar.")
    else:
        with st.spinner("Clustering neighborhoods and optimizing transit routes..."):
            try:
                itinerary = generate_itinerary(preferences, provider, api_key, demo_mode)
                st.session_state.active_itinerary = itinerary
                st.toast("Optimized itinerary generated!", icon="✅")
            except Exception as exc:
                st.error(f"Itinerary generation failed: {exc}")

# ---------------------------------------------------------------------------
# MAIN 4-TAB WORKSPACE
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🌍 1. Smart Destination Recommender",
        "🗺️ 2. Day-by-Day Optimized Itinerary",
        "🎛️ 3. Vibe & Dynamic Activity Swap",
        "💾 4. Trip Management & PDF Export",
    ]
)

# ===========================================================================
# TAB 1: SMART DESTINATION RECOMMENDER (EPIC 3)
# ===========================================================================
with tab1:
    st.subheader("Undecided on Where to Go? Discover Your Top 3 Matches")
    st.caption(
        f"Matching **{preferences['vibe']}** mood • **{preferences['budget']}** budget • "
        f"**{preferences['party']}** • Departing **{preferences['start_date']}**"
    )

    if st.button("🔍 Find Top 3 Matching Destinations", use_container_width=False):
        if not demo_mode and not api_key:
            st.error("Please provide an API key or turn on Demo Mode in the sidebar.")
        else:
            with st.spinner("Analyzing seasonal weather, budget fit, and travel mood..."):
                try:
                    st.session_state.recommended_cities = recommend_destinations(
                        preferences, provider, api_key, demo_mode
                    )
                except Exception as exc:
                    st.error(f"Could not fetch recommendations: {exc}")

    if st.session_state.recommended_cities:
        cols = st.columns(3)
        for idx, rec in enumerate(st.session_state.recommended_cities):
            with cols[idx]:
                full_name = f"{rec['city']}, {rec['country']}"
                inr_daily = int(rec.get("est_daily_usd", 120) * 84)
                tags_html = "".join(
                    f'<span class="tag-pill">{t}</span>' for t in rec.get("tags", [])
                )
                st.markdown(
                    f"""
                    <div class="dest-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#0f4c5c;">{full_name}</h3>
                            <span style="background:#dcfce7; color:#166534; font-weight:700; padding:0.2rem 0.6rem; border-radius:999px; font-size:0.8rem;">
                                {rec.get('match_score', 95)}% Match
                            </span>
                        </div>
                        <p style="color:#475569; font-size:0.86rem; margin:0.5rem 0;">
                            🌤️ <b>Season:</b> {rec.get('weather_note', '')}
                        </p>
                        <p style="color:#0f172a; font-size:0.88rem; margin:0.4rem 0;">
                            💰 <b>Est. Daily Spend:</b> ${rec.get('est_daily_usd', 120)} USD (~₹{inr_daily:,} INR)
                        </p>
                        <p style="color:#334155; font-size:0.88rem; margin:0.6rem 0;">{rec.get('why_it_fits', '')}</p>
                        <div style="margin-top:0.6rem;">{tags_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Select {rec['city']} & Build Plan", key=f"select_dest_{idx}", use_container_width=True):
                    st.session_state.selected_destination = full_name
                    updated_prefs = dict(preferences)
                    updated_prefs["destination"] = full_name
                    with st.spinner(f"Building clustered itinerary for {full_name}..."):
                        st.session_state.active_itinerary = generate_itinerary(
                            updated_prefs, provider, api_key, demo_mode
                        )
                    st.success(f"Loaded {full_name}! Switch to **Tab 2** to view your plan.")
    else:
        st.info("Click **Find Top 3 Matching Destinations** above to get personalized destination recommendations.")

# ===========================================================================
# TAB 2: DAY-BY-DAY OPTIMIZED ITINERARY GENERATOR (EPIC 4)
# ===========================================================================
with tab2:
    itin = st.session_state.active_itinerary
    if not itin:
        st.info(
            "No active itinerary yet. Configure your preferences in the sidebar and click **Generate Optimized Itinerary**."
        )
    else:
        currency = itin.get("local_currency", "USD")
        days = itin.get("days", [])

        # Calculate overall budget totals
        grand_local = sum(
            float(slot.get("cost_local", 0))
            for d in days
            for slot in d.get("slots", [])
        )
        grand_conv = convert_currency(grand_local, currency)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Destination", itin.get("destination", "Custom Trip"))
        m2.metric("Total (Local)", f"{grand_conv['local']:,.0f} {currency}")
        m3.metric("Total (USD)", f"${grand_conv['usd']:,.2f}")
        m4.metric("Total (INR)", f"₹{grand_conv['inr']:,}")

        st.divider()

        running_local = 0.0
        for day in days:
            day_num = day.get("day_number", 1)
            zone = day.get("cluster_zone", "Neighborhood Cluster")
            transit_note = day.get("transit_note", "")

            day_local = sum(float(s.get("cost_local", 0)) for s in day.get("slots", []))
            running_local += day_local
            day_conv = convert_currency(day_local, currency)
            run_conv = convert_currency(running_local, currency)

            st.markdown(
                f"""
                <div class="cluster-header">
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; align-items:center;">
                        <h3 style="margin:0; color:#0f4c5c;">Day {day_num} — 📍 {zone}</h3>
                        <span style="font-size:0.86rem; font-weight:600; color:#9a3412;">
                            Day Est: {day_conv['local']:,.0f} {currency} (${day_conv['usd']:.2f} / ₹{day_conv['inr']:,}) &nbsp;|&nbsp;
                            Running Total: {run_conv['local']:,.0f} {currency} (${run_conv['usd']:.2f})
                        </span>
                    </div>
                    <p style="margin:0.35rem 0 0 0; font-size:0.86rem; color:#475569;">
                        🚇 <b>Zero-Backtrack Logistics:</b> {transit_note}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for slot in day.get("slots", []):
                s_conv = convert_currency(float(slot.get("cost_local", 0)), currency)
                st.markdown(
                    f"""
                    <div class="slot-card">
                        <span class="cost-pill">{s_conv['local']:,.0f} {currency} • ${s_conv['usd']:.2f} • ₹{s_conv['inr']:,}</span>
                        <div>
                            <span class="slot-badge">{slot.get('slot_name', '')}</span>
                            <span style="font-size:0.83rem; color:#64748b; font-weight:600;">🕒 {slot.get('time_window', '')}</span>
                        </div>
                        <h4 style="margin:0.45rem 0 0.25rem 0; color:#0f172a;">{slot.get('title', '')}</h4>
                        <p style="margin:0 0 0.4rem 0; color:#334155; font-size:0.9rem;">{slot.get('description', '')}</p>
                        <div style="font-size:0.8rem; color:#0f4c5c; font-weight:500;">
                            📌 {slot.get('neighborhood', zone)} &nbsp;•&nbsp; 🚶 {slot.get('transit_from_prev', '')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ===========================================================================
# TAB 3: VIBE CUSTOMIZATION & DYNAMIC ACTIVITY SWAP (EPIC 4)
# ===========================================================================
with tab3:
    itin = st.session_state.active_itinerary
    if not itin:
        st.info("Generate an itinerary first in **Tab 1** or **Tab 2** to customize specific slots.")
    else:
        st.subheader("Surgical Day & Slot Customizer")
        st.write(
            "Modify a specific meal, attraction, or entire day without resetting the rest of your trip."
        )

        day_options = [f"Day {d['day_number']}: {d['cluster_zone']}" for d in itin.get("days", [])]
        c1, c2 = st.columns(2)
        with c1:
            selected_day_label = st.selectbox("Select Day to Modify", day_options)
            selected_day_num = int(selected_day_label.split(":")[0].replace("Day ", ""))
        with c2:
            slot_choice = st.selectbox(
                "Select Time Slot",
                [
                    "Morning Sightseeing",
                    "Lunch Recommendation",
                    "Afternoon Leisure",
                    "Evening Dining & Entertainment",
                    "Entire Day",
                ],
            )

        quick_presets = st.pills(
            "Quick Swap Ideas",
            [
                "Swap museum for vibrant outdoor street market",
                "Find authentic 100% vegetarian lunch spot",
                "Make afternoon kid-friendly & relaxed",
                "Upgrade evening to scenic rooftop dining",
            ],
            selection_mode="single",
        )

        custom_instruction = st.text_input(
            "Custom Modification Request",
            value=quick_presets or "",
            placeholder="e.g., Swap museum for outdoor market, or find a cozy specialty coffee shop",
        )

        if st.button("🔄 Regenerate Selected Slot / Day", type="primary"):
            if not custom_instruction.strip():
                st.warning("Please enter or select a modification instruction.")
            elif not demo_mode and not api_key:
                st.error("Please enter an API key or enable Demo Mode.")
            else:
                with st.spinner(f"Updating Day {selected_day_num} ({slot_choice})..."):
                    try:
                        st.session_state.active_itinerary = regenerate_day_or_slot(
                            itinerary=itin,
                            day_number=selected_day_num,
                            target_slot=slot_choice,
                            modification_prompt=custom_instruction.strip(),
                            prefs=preferences,
                            provider=provider,
                            api_key=api_key,
                            demo_mode=demo_mode,
                        )
                        st.success(
                            f"Updated **Day {selected_day_num} — {slot_choice}** while preserving all other days!"
                        )
                    except Exception as exc:
                        st.error(f"Swap failed: {exc}")

        # Live Preview of the Selected Day
        target_day_obj = next(
            (d for d in itin.get("days", []) if d["day_number"] == selected_day_num), None
        )
        if target_day_obj:
            st.markdown(f"#### Current Schedule for Day {selected_day_num} ({target_day_obj['cluster_zone']})")
            for s in target_day_obj.get("slots", []):
                st.markdown(
                    f"- **{s['slot_name']}** ({s['time_window']}): **{s['title']}** — *{s['description']}*"
                )

# ===========================================================================
# TAB 4: TRIP MANAGEMENT & OFFLINE PDF EXPORT (EPIC 5)
# ===========================================================================
with tab4:
    col_save, col_export = st.columns([1.1, 1])

    with col_save:
        st.subheader("💾 Save Current Trip to History")
        if st.session_state.active_itinerary:
            default_title = (
                f"{st.session_state.active_itinerary.get('destination', 'Trip')} "
                f"({len(st.session_state.active_itinerary.get('days', []))}D - {preferences['budget']})"
            )
            custom_trip_name = st.text_input("Trip Bookmark Title", value=default_title)
            if st.button("📌 Save Trip to Workspace", use_container_width=True):
                saved = save_trip(
                    st.session_state,
                    preferences,
                    st.session_state.active_itinerary,
                    trip_title=custom_trip_name,
                )
                st.success(f"Saved **{saved['title']}** (ID: `{saved['trip_id']}`)!")
        else:
            st.info("Generate an itinerary first to save or export it.")

    with col_export:
        st.subheader("📄 Offline PDF Travel Guide")
        if st.session_state.active_itinerary:
            st.write(
                "Includes day-by-day clustered schedules, Local/USD/INR cost breakdown, and an offline emergency contact checklist."
            )
            try:
                pdf_bytes = generate_itinerary_pdf(
                    st.session_state.active_itinerary, preferences
                )
                file_slug = (
                    st.session_state.active_itinerary.get("destination", "itinerary")
                    .lower()
                    .replace(", ", "_")
                    .replace(" ", "_")
                )
                st.download_button(
                    label="⬇️ Download Offline PDF Itinerary Guide",
                    data=pdf_bytes,
                    file_name=f"{file_slug}_travel_guide.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"PDF generation error: {exc}")
        else:
            st.caption("PDF export unlocks automatically once an itinerary is active.")

    st.divider()
    st.subheader("🗂️ Saved Trip History")

    saved_trips = st.session_state.get("saved_trips", [])
    if not saved_trips:
        st.caption("No saved trips yet. Bookmark an itinerary above to build your travel vault.")
    else:
        for trip in saved_trips:
            with st.container(border=True):
                hc1, hc2, hc3 = st.columns([3, 1, 1])
                with hc1:
                    st.markdown(f"**{trip['title']}** &nbsp; `#{trip['trip_id']}`")
                    st.caption(
                        f"Saved: {trip['saved_at']}  |  Party: {trip['preferences'].get('party')}  |  "
                        f"Pace: {trip['preferences'].get('pace')}  |  "
                        f"Interests: {', '.join(trip['preferences'].get('interests', []))}"
                    )
                with hc2:
                    if st.button("📂 Load Trip", key=f"load_{trip['trip_id']}", use_container_width=True):
                        st.session_state.active_itinerary = trip["itinerary"]
                        st.toast(f"Loaded {trip['title']} into active workspace!", icon="🗺️")
                        st.rerun()
                with hc3:
                    if st.button("🗑️ Delete", key=f"del_{trip['trip_id']}", use_container_width=True):
                        delete_trip(st.session_state, trip["trip_id"])
                        st.rerun()
