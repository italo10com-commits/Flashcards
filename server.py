import glob, json, os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(BASE, "por_materia")


def ler(caminho):
    with open(caminho, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def carregar():
    """Lê todos os .txt de por_materia (formato: Frente | Verso | Dica)."""
    materias = []
    for arq in sorted(glob.glob(os.path.join(PASTA, "*.txt"))):
        nome_arq = os.path.splitext(os.path.basename(arq))[0]
        nome = re.sub(r"^\d+_", "", nome_arq).replace("_", " ")
        cards = []
        for i, linha in enumerate(ler(arq).splitlines()):
            p = [x.strip() for x in linha.split("|")]
            if i == 0 and p[0].lower() == "frente":
                continue
            if len(p) < 2 or not p[0] or not p[1]:
                continue
            frente = p[0]
            erradas = []
            if len(p) >= 4:  # Frente | Verso | Dica | Erradas (separadas por ;;)
                verso, dica = p[1], p[2]
                erradas = [x.strip() for x in p[3].split(";;") if x.strip()]
            else:
                verso = " | ".join(p[1:-1]) if len(p) > 2 else p[1]
                dica = p[-1] if len(p) > 2 else ""
            if " - " in frente:  # "Matéria - Tópico"
                prefixo, frente = frente.split(" - ", 1)
                if not cards:
                    nome = prefixo  # usa o nome com acentos do próprio card
            cards.append({"t": frente, "v": verso, "d": dica, "e": erradas})
        if cards:
            materias.append({"id": nome_arq, "nome": nome, "cards": cards})
    return materias


class H(BaseHTTPRequestHandler):
    def responder(self, corpo_body=True):
        rota = self.path.split("?")[0]
        if rota == "/api/cards":
            corpo, tipo = json.dumps(carregar(), ensure_ascii=False).encode(), "application/json; charset=utf-8"
        elif rota in ("/", "/index.html"):
            with open(os.path.join(BASE, "index.html"), "rb") as f:
                corpo, tipo = f.read(), "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if corpo_body:
            self.wfile.write(corpo)

    def do_GET(self):
        self.responder()

    def do_HEAD(self):
        self.responder(False)


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    print(f"Rodando em http://localhost:{porta}")
    ThreadingHTTPServer(("0.0.0.0", porta), H).serve_forever()
