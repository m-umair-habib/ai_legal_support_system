"""
🔥 Smart Lawyer Loader - Fully Automated Fair Rotation System
No fixed lines. No hardcoded lawyers. Complete automation.
Every lawyer gets equal opportunity through smart randomization.
"""

import pandas as pd
from pathlib import Path
from .config import LAWYERS_DIR
from accounts.models import LawyerProfile as DB_LawyerProfile
import random
from collections import defaultdict
import time


class LawyerLoader:
    def __init__(self):
        self.lawyers = []
        self.impression_tracker = defaultdict(int)  # Track how many times each lawyer was shown
        self.last_shown_tracker = {}  # Track when each lawyer was last shown
        self.load_all_lawyers()
        self._initialize_trackers()

    def _initialize_trackers(self):
        """Initialize tracking for all lawyers"""
        for lawyer in self.lawyers:
            lawyer_id = lawyer['id']
            self.impression_tracker[lawyer_id] = 0
            self.last_shown_tracker[lawyer_id] = 0

    def load_all_lawyers(self):
        """Load lawyers from all available sources automatically"""
        self.lawyers = []
        sequential_id = 1

        # ==================== LOAD FROM CSV FILES ====================
        csv_files = list(LAWYERS_DIR.glob('*.csv'))
        print(f"\n📁 Found {len(csv_files)} CSV file(s)")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                print(f"   📄 Loading: {csv_file.name} ({len(df)} records)")
                
                for _, row in df.iterrows():
                    specialties = self._extract_specialties(row)
                    
                    lawyer = {
                        'id': sequential_id,
                        'name': self._clean_text(row.get('name', 'Unknown Lawyer')),
                        'specialty': ', '.join(specialties) if specialties else 'General Practice',
                        'specialty_list': specialties or ['General'],
                        'location': self._clean_text(row.get('location', 'Lahore, Pakistan')),
                        'experience': self._clean_text(row.get('experience', 'N/A')),
                        'phone': self._clean_text(row.get('phone', '')),
                        'email': self._clean_text(row.get('email', '')),
                        'source': 'csv',
                        'source_file': csv_file.name
                    }
                    self.lawyers.append(lawyer)
                    sequential_id += 1
                    
            except Exception as e:
                print(f"   ⚠️ Error loading {csv_file.name}: {e}")

        # ==================== LOAD FROM DATABASE ====================
        try:
            db_lawyers = DB_LawyerProfile.objects.filter(is_approved=True)
            print(f"\n🗄️ Loading {db_lawyers.count()} approved lawyers from database")
            
            for db in db_lawyers:
                name = f"{db.user.first_name} {db.user.last_name}".strip() or db.user.username
                specialties = [s.strip() for s in str(db.case_specialty or "").split(",") if s.strip()]
                
                lawyer = {
                    'id': db.id,
                    'name': name,
                    'specialty': ', '.join(specialties) if specialties else 'General Practice',
                    'specialty_list': specialties or ['General'],
                    'location': str(db.location) if db.location else 'Pakistan',
                    'experience': f"{db.years_experience} Years" if db.years_experience else 'N/A',
                    'phone': str(getattr(db.user, 'contact_number', '')),
                    'email': str(db.user.email),
                    'source': 'database',
                    'source_file': 'database'
                }
                self.lawyers.append(lawyer)
                
        except Exception as e:
            print(f"⚠️ Database load error: {e}")

        print(f"\n✅ TOTAL lawyers loaded: {len(self.lawyers)}")
        print(f"   📊 CSV: {sum(1 for l in self.lawyers if l['source'] == 'csv')}")
        print(f"   📊 Database: {sum(1 for l in self.lawyers if l['source'] == 'database')}\n")

    def _extract_specialties(self, row):
        """Automatically extract specialties from any column format"""
        specialties = []
        
        # Check all possible column names
        for col in ['speciality', 'specialty', 'specialties', 'expertise', 'practice_areas']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).strip()
                
                # Handle list format: "[Civil, Criminal]"
                if val.startswith('[') and val.endswith(']'):
                    try:
                        specialties = eval(val)
                        if isinstance(specialties, list):
                            break
                    except:
                        specialties = [val.strip('[]')]
                
                # Handle comma separated: "Civil, Criminal, Family"
                elif ',' in val:
                    specialties = [s.strip() for s in val.split(',') if s.strip()]
                    break
                
                # Single specialty
                else:
                    specialties = [val]
                    break
        
        return specialties if specialties else ['General Practice']

    def _clean_text(self, text):
        """Clean and normalize text"""
        if pd.isna(text):
            return ''
        return str(text).strip()

    def _calculate_relevance_score(self, query, lawyer):
        """Calculate how relevant a lawyer is for the query"""
        query_lower = query.lower()
        score = 0
        
        specialty_text = " ".join(lawyer.get('specialty_list', [])).lower()
        specialty_text += " " + lawyer.get('specialty', '').lower()
        location_text = lawyer.get('location', '').lower()
        name_text = lawyer.get('name', '').lower()

        # ==================== CATEGORY MATCHING ====================
        categories = {
            'criminal': {
                'keywords': ['قتل', 'murder', '302', 'theft', 'chori', '379', 'rape', '376', 
                           '420', 'fir', 'criminal', 'dacoity', 'bail', 'fauj', 'robbery', '392',
                           'qatl', 'zina', 'hudood', 'blasphemy', '295', 'terrorism'],
                'specialty_match': ['criminal', 'قانون فوجداری', 'crime', 'fauj', 'criminal law'],
                'weight': 25
            },
            'civil': {
                'keywords': ['property', 'suit', 'dispute', 'civil', 'plaint', 'inheritance', 
                           'مال', 'jaidad', 'wakalat', 'contract', 'damages', 'recovery',
                           'rent', 'ejectment', 'specific performance'],
                'specialty_match': ['civil', 'property', 'inheritance', 'contract', 'civil law'],
                'weight': 22
            },
            'family': {
                'keywords': ['divorce', 'طلاق', 'خلع', 'khula', 'family', 'maintenance', 'nafqa',
                           'custody', 'guardianship', 'marriage', 'nikah', 'dower', 'haq mehr',
                           'children', 'wife', 'husband', 'خاندان'],
                'specialty_match': ['family', 'divorce', 'marriage', 'خاندانی', 'family law'],
                'weight': 22
            },
            'constitutional': {
                'keywords': ['constitution', 'writ', 'rights', 'high court', 'fundamental', 
                           'آئین', 'دستور', 'supreme court', 'article', 'petition',
                           'habeas corpus', 'mandamus', 'certiorari'],
                'specialty_match': ['constitutional', 'writ', 'high court', 'supreme court', 'constitution'],
                'weight': 20
            },
            'corporate': {
                'keywords': ['company', 'corporate', 'tax', 'income tax', 'sales tax', 'secp',
                           'registration', 'trademark', 'copyright', 'patent', 'merger',
                           'acquisition', 'securities', 'stock exchange'],
                'specialty_match': ['corporate', 'tax', 'commercial', 'company', 'business'],
                'weight': 18
            },
            'labour': {
                'keywords': ['labour', 'employment', 'worker', 'factory', 'wages', 'termination',
                           'مزدور', 'industrial', 'eobi', 'social security'],
                'specialty_match': ['labour', 'employment', 'service', 'industrial'],
                'weight': 18
            }
        }

        # Apply category weights
        for category, config in categories.items():
            if any(kw in query_lower for kw in config['keywords']):
                if any(kw in specialty_text for kw in config['specialty_match']):
                    score += config['weight']

        # ==================== KEYWORD MATCHING ====================
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2:
                if word in specialty_text:
                    score += 3
                if word in location_text:
                    score += 2
                if word in name_text:
                    score += 1

        # ==================== EXPERIENCE BONUS ====================
        exp = lawyer.get('experience', '').lower()
        if '20+' in exp or '25+' in exp or '30+' in exp:
            score += 8
        elif '15+' in exp or '10+' in exp:
            score += 5
        elif '5+' in exp or '5-10' in exp:
            score += 3

        # ==================== VERIFIED BONUS ====================
        if lawyer.get('source') == 'database':
            score += 5  # Database lawyers are verified

        return score

    def get_lawyer_by_id(self, lawyer_id):
        """Retrieve lawyer by ID"""
        for lawyer in self.lawyers:
            if lawyer['id'] == lawyer_id:
                return lawyer
        return None

    def search_by_specialty(self, query, top_k=5):
        """
        Smart search with fair rotation.
        Automatically balances relevance with equal opportunity.
        """
        if not self.lawyers:
            return []

        # ==================== EMPTY QUERY ====================
        if not query or len(query.strip()) < 3:
            # Return least recently shown lawyers
            candidates = sorted(self.lawyers, 
                              key=lambda l: (self.last_shown_tracker[l['id']], 
                                           self.impression_tracker[l['id']]))
            selected = candidates[:top_k]
            self._update_tracking(selected)
            return selected

        # ==================== SCORE ALL LAWYERS ====================
        scored_lawyers = []
        for lawyer in self.lawyers:
            relevance_score = self._calculate_relevance_score(query, lawyer)
            
            # Fairness adjustment: Reduce score for frequently shown lawyers
            impression_penalty = min(self.impression_tracker[lawyer['id']] * 0.5, 10)
            
            # Time-based boost: Boost lawyers not shown recently
            time_since_last_shown = time.time() - self.last_shown_tracker[lawyer['id']]
            time_boost = min(time_since_last_shown / 3600, 5)  # Max 5 points boost per hour
            
            # Random factor for natural variation
            random_factor = random.uniform(0, 3)
            
            final_score = relevance_score - impression_penalty + time_boost + random_factor
            
            scored_lawyers.append((final_score, relevance_score, lawyer))

        # ==================== SELECTION PROCESS ====================
        # Sort by final score
        scored_lawyers.sort(key=lambda x: x[0], reverse=True)
        
        # Create candidate pool (top 3x lawyers)
        pool_size = min(len(scored_lawyers), top_k * 3)
        candidate_pool = scored_lawyers[:pool_size]
        
        # Weighted random selection from pool
        selected = []
        available = list(candidate_pool)
        
        while len(selected) < top_k and available:
            # Calculate weights (higher score = higher chance)
            total_score = sum(score for score, _, _ in available)
            if total_score == 0:
                # Random if all scores zero
                choice = random.choice(available)
            else:
                # Weighted random selection
                weights = [score / total_score for score, _, _ in available]
                choice = random.choices(available, weights=weights, k=1)[0]
            
            selected.append(choice[2])
            available.remove(choice)

        # ==================== FALLBACK ====================
        if len(selected) < top_k:
            remaining = [l for l in self.lawyers if l not in selected]
            if remaining:
                needed = top_k - len(selected)
                # Get least impressed lawyers
                remaining.sort(key=lambda l: (self.impression_tracker[l['id']], 
                                             self.last_shown_tracker[l['id']]))
                selected.extend(remaining[:needed])

        # ==================== FINAL SHUFFLE ====================
        random.shuffle(selected)
        
        # Update tracking
        self._update_tracking(selected)
        
        return selected

    def _update_tracking(self, shown_lawyers):
        """Update impression counts and last shown timestamps"""
        current_time = time.time()
        for lawyer in shown_lawyers:
            lawyer_id = lawyer['id']
            self.impression_tracker[lawyer_id] += 1
            self.last_shown_tracker[lawyer_id] = current_time

    def get_statistics(self):
        """Get impression statistics for monitoring"""
        if not self.lawyers:
            return {}
        
        impressions = list(self.impression_tracker.values())
        return {
            'total_lawyers': len(self.lawyers),
            'total_impressions': sum(impressions),
            'avg_impressions': sum(impressions) / len(impressions) if impressions else 0,
            'max_impressions': max(impressions) if impressions else 0,
            'min_impressions': min(impressions) if impressions else 0,
        }


# ==================== SINGLETON PATTERN ====================
_loader = None

def get_lawyer_loader():
    """Get or create singleton instance"""
    global _loader
    if _loader is None:
        _loader = LawyerLoader()
    return _loader


def refresh_lawyer_loader():
    """Force refresh the lawyer loader (called when lawyers are added/removed)"""
    global _loader
    _loader = LawyerLoader()
    print("🔄 Lawyer loader refreshed with fresh data")
    return _loader


def get_loader_statistics():
    """Get current loader statistics"""
    loader = get_lawyer_loader()
    return loader.get_statistics()