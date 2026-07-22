def formatar_data(data_iso):
    """'2026-07-17' ou '2026-07-17 12:47:16' -> '17/07/2026'"""

    if not data_iso:
        return ""

    data_parte = data_iso.split(" ")[0]
    ano, mes, dia = data_parte.split("-")

    return f"{dia}/{mes}/{ano}"


def formatar_data_hora(data_iso):
    """'2026-07-17 12:47:16' -> '17/07/2026 12:47'"""

    if not data_iso:
        return ""

    data_parte, _, hora_parte = data_iso.partition(" ")
    ano, mes, dia = data_parte.split("-")

    if not hora_parte:
        return f"{dia}/{mes}/{ano}"

    return f"{dia}/{mes}/{ano} {hora_parte[:5]}"
