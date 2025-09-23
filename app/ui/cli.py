from app.router.safety_router import route
from app.retriever.retriever import retrieve
from app.answer.compose import from_chunks, crisis_message, template_for, disclaimer
from app.ui.audit import log

def respond(msg: str) -> str:
    r = route(msg)
    if r and r.auto_reply_key == "crisis":
        log("route", r.level)
        return crisis_message()
    if r:
        log("route", r.level)
        return template_for(r.auto_reply_key)
    log("route", None)
    return from_chunks(retrieve(msg))

if __name__ == "__main__":
    print(disclaimer())
    print("RIH Assistant CLI — type 'exit' to quit\n")
    while True:
        q = input("> ").strip()
        if q.lower() in {"exit","quit"}:
            break
        print(respond(q), "\n")
