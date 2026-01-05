import re
import os

def extract_text(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    extracted_lines = []
    capture = False
    
    for line in lines:
        stripped = line.strip()
        
        if "Final Output:" in line:
            capture = True
            parts = line.split("Final Output:")
            if len(parts) > 1:
                content = parts[1].strip()
                content = content.replace("│", "").strip()
                extracted_lines.append(content)
            continue
            
        if capture:
            if "╰" in line:
                break
            
            content = stripped.replace("│", "").strip()
            if content:
                extracted_lines.append(content)

    full_text = " ".join(extracted_lines)
    return full_text

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
            next_char = parts[i+1][0] if parts[i+1] else ""
            
            sep = "**"
            
            if i % 2 == 0: # Abriendo negrita (Plain -> Bold)
                # Separar si el caracter anterior es alfanumérico (pegado a palabra)
                if prev_char.isalnum():
                    sep = "\n\n**"
            else: # Cerrando negrita (Bold -> Plain)
                # Separar si el caracter siguiente es alfanumérico (pegado a palabra)
                # Esto mantiene la puntuación pegada a la negrita (ej: **Bold**:)
                if next_char.isalnum():
                    sep = "**\n\n"
            
            result.append(sep)
            
    return "".join(result)

def format_news_article(raw_text):
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

if __name__ == "__main__":
    input_file = "as.txt"
    output_file = "noticia_formateada.md"
    
    if not os.path.exists(input_file):
        print(f"Error: No se encuentra el archivo {input_file}")
        exit(1)
        
    raw_text = extract_text(input_file)
    
    if not raw_text:
        print("ERROR: No se extrajo texto.")
        exit(1)
        
    formatted_text = format_news_article(raw_text)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_text)
        
    print(f"Resultado guardado en: {output_file}")
