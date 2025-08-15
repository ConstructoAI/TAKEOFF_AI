import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
from typing import Optional, Tuple, List, Dict

class PDFProcessor:
    """Gestionnaire pour le traitement des fichiers PDF"""
    
    def __init__(self):
        self.pdf_document = None
        self.current_page = None
        self.zoom_level = 2.0  # Zoom par défaut pour une meilleure qualité
    
    def load_pdf(self, pdf_path: str) -> bool:
        """Charge un fichier PDF"""
        try:
            self.pdf_document = fitz.open(pdf_path)
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du PDF: {e}")
            return False
    
    def get_page_count(self) -> int:
        """Retourne le nombre de pages du PDF"""
        if self.pdf_document:
            return len(self.pdf_document)
        return 0
    
    def get_page_image(self, page_number: int, zoom: float = None) -> Optional[Image.Image]:
        """Convertit une page PDF en image PIL"""
        if not self.pdf_document or page_number >= len(self.pdf_document):
            return None
        
        try:
            page = self.pdf_document[page_number]
            zoom = zoom or self.zoom_level
            
            # Créer une matrice de transformation pour le zoom
            mat = fitz.Matrix(zoom, zoom)
            
            # Rendre la page en pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convertir en image PIL
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            return img
            
        except Exception as e:
            print(f"Erreur lors de la conversion de la page: {e}")
            return None
    
    def get_page_text(self, page_number: int) -> str:
        """Extrait le texte d'une page"""
        if not self.pdf_document or page_number >= len(self.pdf_document):
            return ""
        
        try:
            page = self.pdf_document[page_number]
            return page.get_text()
        except Exception as e:
            print(f"Erreur lors de l'extraction du texte: {e}")
            return ""
    
    def get_all_text(self) -> str:
        """Extrait tout le texte du PDF"""
        if not self.pdf_document:
            return ""
        
        all_text = []
        for page_num in range(len(self.pdf_document)):
            text = self.get_page_text(page_num)
            if text:
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n\n".join(all_text)
    
    def extract_lines(self, page_number: int, threshold: float = 10.0) -> List[Dict]:
        """Extrait les lignes d'une page PDF"""
        if not self.pdf_document or page_number >= len(self.pdf_document):
            return []
        
        try:
            page = self.pdf_document[page_number]
            drawings = page.get_drawings()
            
            lines = []
            for drawing in drawings:
                for item in drawing.get("items", []):
                    if item[0] == "l":  # Line
                        p1 = item[1]
                        p2 = item[2]
                        
                        # Calculer la longueur
                        length = np.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
                        
                        if length >= threshold:
                            lines.append({
                                'start': (p1.x, p1.y),
                                'end': (p2.x, p2.y),
                                'length': length
                            })
            
            return lines
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des lignes: {e}")
            return []
    
    def get_page_size(self, page_number: int) -> Tuple[float, float]:
        """Retourne la taille d'une page en points"""
        if not self.pdf_document or page_number >= len(self.pdf_document):
            return (0, 0)
        
        try:
            page = self.pdf_document[page_number]
            rect = page.rect
            return (rect.width, rect.height)
        except Exception as e:
            print(f"Erreur lors de la récupération de la taille: {e}")
            return (0, 0)
    
    def close(self):
        """Ferme le document PDF"""
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None
    
    def search_text(self, search_term: str, page_number: Optional[int] = None) -> List[Dict]:
        """Recherche du texte dans le PDF"""
        if not self.pdf_document:
            return []
        
        results = []
        
        # Déterminer les pages à chercher
        if page_number is not None:
            pages = [page_number] if page_number < len(self.pdf_document) else []
        else:
            pages = range(len(self.pdf_document))
        
        for page_num in pages:
            try:
                page = self.pdf_document[page_num]
                text_instances = page.search_for(search_term)
                
                for inst in text_instances:
                    results.append({
                        'page': page_num,
                        'rect': {
                            'x': inst.x0,
                            'y': inst.y0,
                            'width': inst.x1 - inst.x0,
                            'height': inst.y1 - inst.y0
                        },
                        'text': search_term
                    })
            except Exception as e:
                print(f"Erreur lors de la recherche sur la page {page_num}: {e}")
        
        return results