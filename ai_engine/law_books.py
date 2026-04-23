"""Law Books Manager - Handles loading and processing of law books"""
import os
from pathlib import Path
from .config import LAW_BOOKS_DIR, LAW_BOOKS

class LawBooksManager:
    """Manage all law books and their status"""
    
    def __init__(self):
        self.law_books = LAW_BOOKS
        self.available_books = []
        self.check_availability()
    
    def check_availability(self):
        """Check which law books are available in the data folder"""
        print("\n📚 Checking Law Books Availability")
        print("=" * 40)
        
        for key, info in self.law_books.items():
            file_path = LAW_BOOKS_DIR / info['file']
            if file_path.exists():
                self.available_books.append(key)
                print(f"✅ {info['name']} - Available")
                print(f"   📁 Path: {file_path}")
                print(f"   📏 Size: {file_path.stat().st_size / 1024:.1f} KB")
            else:
                print(f"❌ {info['name']} - MISSING")
                print(f"   Expected at: {file_path}")
        
        print(f"\n📊 Summary: {len(self.available_books)}/{len(self.law_books)} law books available")
        print("=" * 40)
        
        return self.available_books
    
    def get_book_info(self, book_key):
        """Get information about a specific law book"""
        return self.law_books.get(book_key)
    
    def get_all_available(self):
        """Get list of all available law books"""
        return [self.law_books[key] for key in self.available_books]
    
    def is_available(self, book_key):
        """Check if a specific law book is available"""
        return book_key in self.available_books

# Test function
def test_law_books():
    """Test law books manager"""
    print("\n" + "=" * 50)
    print("📚 TESTING LAW BOOKS MANAGER")
    print("=" * 50)
    
    manager = LawBooksManager()
    
    print("\nAvailable Books:")
    for book in manager.get_all_available():
        print(f"  - {book['name']}")
    
    print("\n✅ Law Books Manager test complete!\n")