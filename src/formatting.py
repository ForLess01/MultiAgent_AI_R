import re


def fix_bold_spacing(text):
    """
    Corrige el espaciado alrededor de marcadores de negrita (**).
    Usa isalnum() para decidir si separar, evitando separar puntuación.
    """
    parts = text.split("**")
    if len(parts) < 2:
        return text

    result = []
    for i in range(len(parts)):
        part = parts[i]
        result.append(part)

        if i < len(parts) - 1:
            prev_char = part[-1] if part else ""
            next_char = parts[i + 1][0] if parts[i + 1] else ""

            sep = "**"

            if i % 2 == 0:  # Abriendo negrita (Plain -> Bold)
                # Separar si el caracter anterior es alfanumérico (pegado a palabra)
                if prev_char.isalnum():
                    sep = "\n\n**"
            else:  # Cerrando negrita (Bold -> Plain)
                # Separar si el caracter siguiente es alfanumérico (pegado a palabra)
                # Esto mantiene la puntuación pegada a la negrita (ej: **Bold**:)
                if next_char.isalnum():
                    sep = "**\n\n"

            result.append(sep)

    return "".join(result)


def format_news_article(raw_text):
    """
    Toma un texto crudo generado por un LLM que ha perdido formato y lo reestructura
    como un artículo de periódico legible en Markdown.
    """
    if not raw_text:
        return ""

    # 0. Normalizar espacios
    formatted = re.sub(r"\s+", " ", raw_text)

    # 1. Asegurar saltos de línea antes de los encabezados (##, ###)
    formatted = re.sub(r"([^\n])(#+ )", r"\1\n\n\2", formatted)

    # 2. Asegurar saltos de línea antes de citas (>)
    formatted = re.sub(r"([^\n])(> )", r"\1\n\n\2", formatted)

    # 3. Asegurar saltos de línea antes de listas (-)
    formatted = re.sub(r"([^\n])(- \*\*)", r"\1\n\n\2", formatted)
    formatted = re.sub(r"([^\n])(- [A-Z])", r"\1\n\n\2", formatted)

    # 4. Corregir espaciado de negritas
    formatted = fix_bold_spacing(formatted)

    # 5. Separar la sección de fuentes (---)
    formatted = re.sub(r"([^\n])(---)", r"\1\n\n\2", formatted)
    formatted = re.sub(r"(---)([^\n])", r"\1\n\n\2", formatted)

    # 6. Separar texto pegado (CamelCase accidental: "HechosLa", "VenezuelaLa")
    formatted = re.sub(r"([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])", r"\1\n\n\2", formatted)

    # 7. Limpieza general
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)

    return formatted
