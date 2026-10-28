# -*- coding: utf-8 -*-
"""O nome do HTML gerado, num lugar so: render, sonda e portao importam daqui. O
servidor (server.mjs) abre sozinho o mockup-call-to-crm_<data>.html mais novo da
pasta. A edicao anterior (2026-10-27, v3: Teams e 8 campos) fica ao lado, intacta."""
import os

NOME = "mockup-call-to-crm_2026-10-28.html"
HTML = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), NOME)
