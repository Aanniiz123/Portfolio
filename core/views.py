from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import ContactMessage, VideoProject
from .rag import answer as rag_answer

logger = logging.getLogger("core.chat")


def home(request):
    """Landing page — atmospheric hero, services, creative style, contact CTA."""
    services = [
        {
            "title": "Music Video Edits",
            "body": "Edits that feel connected to the track — rhythm, pace, and emotion locked to the sound.",
        },
        {
            "title": "Visualizers",
            "body": "Audio-reactive and rhythmic visualizers that give a song a face and a body.",
        },
        {
            "title": "Cinematic Edits",
            "body": "Moody, atmospheric sequences with cinematic pacing, framing, and colour tone.",
        },
        {
            "title": "Artist Promo Visuals",
            "body": "Releases, drops, and rollouts — teasers, cover artwork motion, and short promos.",
        },
        {
            "title": "Typography & Lyric Visuals",
            "body": "Type-led motion pieces and lyric videos that hold attention and reinforce the song.",
        },
        {
            "title": "Atmospheric & Experimental",
            "body": "Abstract, mood-driven visuals — texture, light, and movement built to feel like a feeling.",
        },
        {
            "title": "Social Content for Artists",
            "body": "Short-form vertical edits and assets designed to live natively on social feeds.",
        },
        {
            "title": "Spiritual & Artistic Concepts",
            "body": "Symbolic, Thangka-inspired, and contemplative visual pieces for select projects.",
        },
    ]

    influences = [
        "Experimental",
        "Music Driven",
        "Surreal",
        "Rhythmic",
        "Visual",
        "Spiritual",
        "Immersive",
        "Artistic",
    ]

    software = [
        "Adobe After Effects",
        "Adobe Premiere Pro",
        "CapCut",
    ]

    experience = [
        "Music & cinematic projects",
        "Storytelling & atmosphere",
        "Artistic & spiritual visuals",
        "Experimental visual work",
    ]

    socials = [
        {
            "name":   "Instagram",
            "handle": "@daamihoni",
            "url":    "https://www.instagram.com/daamihoni",
        },
        {
            "name":   "TikTok",
            "handle": "@avishek_4",
            "url":    "https://www.tiktok.com/@avishek_4",
        },
        {
            "name":   "YouTube",
            "handle": "@no_cturnal",
            "url":    "https://www.youtube.com/@no_cturnal",
        },
    ]

    return render(request, "core/home.html", {
        "services": services,
        "influences": influences,
        "software": software,
        "experience": experience,
        "socials": socials,
        "hero_video_url": settings.HERO_VIDEO_URL,
    })


def work(request):
    """Dedicated work page — all video projects with thumbnails."""
    projects = list(
        VideoProject.objects.all().order_by("order", "-created_at")
    )
    return render(request, "core/work.html", {
        "projects": projects,
    })


def about(request):
    """About page — bio, quick facts, experience timeline, approach."""
    quick_facts = [
        ("Creative name",     "NOCT"),
        ("Based in",          "Nepal"),
        ("Role",              "Freelance Video Editor & Visual Artist"),
        ("Primary tool",      "Adobe After Effects"),
        ("Experience",        "1.5+ months active editing & visual production"),
        ("Focus",             "Music visuals · cinematic · artist collaboration"),
        ("Looking for",       "Musicians · rappers · singers · producers · indie artists"),
        ("Email",             "trippiextgamer@gmail.com"),
    ]

    experience = [
        {
            "role":   "Freelance Video Editor & Visual Artist",
            "where":  "NOCT — Self-employed",
            "period": "2024 — Present",
            "body":   "Building a portfolio of music-driven visual work — music video edits, visualizers, lyric visuals, cinematic sequences, and artist promo content, all cut primarily in Adobe After Effects.",
        },
        {
            "role":   "Music & Atmospheric Projects",
            "where":  "Selected creative work",
            "period": "+1.5yrs",
            "body":   "Developed cinematic edits with a strong focus on mood, visual flow, and emotional tone — combining rhythm, typography, and effects so the visuals feel connected to the track rather than placed on top of it.",
        },
        {
            "role":   "Artistic & Spiritual Visuals",
            "where":  "Concept & experimental work",
            "period": "+1.5yrs",
            "body":   "Produced creative visual pieces inspired by Thangka art, symbolism, and atmospheric storytelling — exploring identity, mood, and meaning through texture and motion.",
        },
    ]

    approach = [
        ("Feel first",        "Start from the emotion in the track, not the footage. Mood and pacing drive every choice."),
        ("Rhythm & timing",   "Cuts that breathe with the music. Timing, breath, and silence are part of the design."),
        ("Atmosphere",        "Lighting, colour, texture, and motion working together to build a world the listener can step into."),
        ("Authentic to you",  "Visuals should feel like the artist, not like a template. The story belongs to the music."),
    ]

    return render(request, "core/about.html", {
        "quick_facts": quick_facts,
        "experience":  experience,
        "approach":    approach,
    })


def contact_view(request):
    """Contact page — renders the form and handles submissions."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            instance = form.save()

            full_message = (
                f"From: {instance.name} <{instance.email}>\n\n"
                f"{instance.message}"
            )

            try:
                send_mail(
                    subject=f"NOCT Portfolio Contact: {instance.subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    using="default",
                )
            except Exception:
                messages.warning(
                    request,
                    "Your message was saved, but the email notification failed to send.",
                )
            else:
                messages.success(request, "Your message has been sent — I'll reply soon.")

            return redirect("contact")
    else:
        form = ContactForm()

    return render(request, "core/contact.html", {"form": form})


# ---------- Chat endpoint --------------------------------------------------

@csrf_exempt
@require_POST
def chat_api(request):
    """POST /api/chat/ — accepts {message, history} and returns {answer, sources}."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "bad_json"}, status=400)

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "empty_message"}, status=400)

    history = payload.get("history") or []
    if not isinstance(history, list):
        history = []

    result = rag_answer(message, history)

    status = 200
    if result.get("error"):
        status = 503
    return JsonResponse(result, status=status)
