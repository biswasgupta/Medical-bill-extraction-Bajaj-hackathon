from typing import List, Set
from rapidfuzz import fuzz
import re

from config import Config
from models import BillItem, PageWiseLineItems, PageType


class DeduplicationEngine:
    """Handle deduplication and aggregation detection"""
    
    def __init__(self):
        self.aggregation_keywords = [kw.lower() for kw in Config.AGGREGATION_KEYWORDS]
    
    def is_aggregation_row(self, item: BillItem) -> bool:
        """
        Check if an item is an aggregation/subtotal row
        
        Args:
            item: BillItem to check
            
        Returns:
            True if item is an aggregation row
        """
        item_name_lower = item.item_name.lower().strip()
        
        # Check against keyword list
        for keyword in self.aggregation_keywords:
            if keyword in item_name_lower:
                return True
        
        # Additional patterns
        # Pattern 1: Just category name with amount (e.g., "Consultation" as a row)
        category_names = [
            "consultation", "drugs", "investigations", "procedures",
            "room rent", "surgery", "pharmacy", "laboratory",
            "equipment", "nursing", "ward charges", "ot charges"
        ]
        
        if item_name_lower in category_names:
            return True
        
        # Pattern 2: Contains only category code like "(999311)"
        if re.match(r'^\([0-9]+\)$', item_name_lower.strip()):
            return True
        
        return False
    
    def build_item_hash(self, item: BillItem, page_no: str = "") -> str:
        """
        Build unique hash for an item
        
        Args:
            item: BillItem
            page_no: Optional page number for context
            
        Returns:
            Hash string
        """
        # Normalize name (remove extra whitespace)
        name = " ".join(item.item_name.split())
        
        # Build hash from key fields
        hash_str = f"{name}|{item.item_rate:.2f}|{item.item_quantity:.2f}|{item.item_amount:.2f}|{page_no}"
        return hash_str
    
    def are_items_similar(
        self, 
        item1: BillItem, 
        item2: BillItem,
        threshold: int = None
    ) -> bool:
        """
        Check if two items are similar enough to be duplicates
        
        Args:
            item1: First item
            item2: Second item
            threshold: Similarity threshold (default from config)
            
        Returns:
            True if items are likely duplicates
        """
        if threshold is None:
            threshold = Config.FUZZY_MATCH_THRESHOLD
        
        # Fuzzy match on name
        name_similarity = fuzz.ratio(
            item1.item_name.lower(),
            item2.item_name.lower()
        )
        
        if name_similarity < threshold:
            return False
        
        # Check if amounts match exactly
        if abs(item1.item_amount - item2.item_amount) > 0.01:
            return False
        
        # Check if rates match exactly
        if abs(item1.item_rate - item2.item_rate) > 0.01:
            return False
        
        # Check if quantities match
        if abs(item1.item_quantity - item2.item_quantity) > 0.01:
            return False
        
        return True
    
    def deduplicate_items(
        self, 
        items: List[BillItem],
        use_fuzzy: bool = True
    ) -> List[BillItem]:
        """
        Remove duplicate items from list
        
        Args:
            items: List of BillItems
            use_fuzzy: Whether to use fuzzy matching
            
        Returns:
            Deduplicated list of BillItems
        """
        if not items:
            return []
        
        unique_items = []
        seen_hashes: Set[str] = set()
        
        for item in items:
            # First check: exact hash match
            item_hash = self.build_item_hash(item)
            
            if item_hash in seen_hashes:
                continue  # Skip duplicate
            
            # Second check: fuzzy similarity (if enabled)
            is_duplicate = False
            if use_fuzzy:
                for unique_item in unique_items:
                    if self.are_items_similar(item, unique_item):
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_items.append(item)
                seen_hashes.add(item_hash)
        
        return unique_items
    
    def filter_aggregations(self, items: List[BillItem]) -> List[BillItem]:
        """
        Filter out aggregation/subtotal rows
        
        Args:
            items: List of BillItems
            
        Returns:
            Filtered list without aggregations
        """
        return [item for item in items if not self.is_aggregation_row(item)]
    
    def process_pagewise_items(
        self,
        pagewise_items: List[PageWiseLineItems]
    ) -> List[BillItem]:
        """
        Process all pages and return unique line items
        
        Args:
            pagewise_items: List of PageWiseLineItems
            
        Returns:
            Deduplicated list of all line items
        """
        all_items = []
        
        for page in pagewise_items:
            # Skip ONLY true summary pages (Final Bill with no line items)
            if page.page_type == PageType.FINAL_BILL and len(page.bill_items) == 0:
                print(f"⚠️ Skipping page {page.page_no} (Final Bill summary with no items)")
                continue

            # If Final Bill page has items, it's likely itemized - process it
            if page.page_type == PageType.FINAL_BILL and len(page.bill_items) > 0:
                print(f"📄 Page {page.page_no}: Processing Final Bill page with {len(page.bill_items)} items (likely itemized)")

            # Filter aggregations from this page
            filtered_items = self.filter_aggregations(page.bill_items)
            print(f"   {len(page.bill_items)} items → {len(filtered_items)} after filtering aggregations")

            all_items.extend(filtered_items)
        
        # Deduplicate across all pages
        unique_items = self.deduplicate_items(all_items, use_fuzzy=True)
        print(f"✅ Total unique items after deduplication: {len(unique_items)}")
        
        return unique_items
    
    def calculate_total(self, items: List[BillItem]) -> float:
        """Calculate total amount from items"""
        return sum(item.item_amount for item in items)
    
    def validate_extraction(
        self,
        unique_items: List[BillItem],
        expected_total: float = None
    ) -> dict:
        """
        Validate extraction quality
        
        Args:
            unique_items: List of unique items
            expected_total: Expected bill total (if known)
            
        Returns:
            Dictionary with validation metrics
        """
        ai_total = self.calculate_total(unique_items)
        
        result = {
            "item_count": len(unique_items),
            "ai_total": round(ai_total, 2)
        }
        
        if expected_total is not None:
            difference = abs(ai_total - expected_total)
            accuracy = 1 - (difference / expected_total) if expected_total > 0 else 0
            
            result.update({
                "expected_total": round(expected_total, 2),
                "difference": round(difference, 2),
                "accuracy_percentage": round(accuracy * 100, 2)
            })
        
        return result


# Test function
def test_deduplication():
    """Test deduplication logic"""
    from models import BillItem
    
    engine = DeduplicationEngine()
    
    # Test items
    items = [
        BillItem(item_name="Consultation", item_amount=1000.0, item_rate=1000.0, item_quantity=1.0),
        BillItem(item_name="Consultation", item_amount=1000.0, item_rate=1000.0, item_quantity=1.0),  # Duplicate
        BillItem(item_name="NICU Charges", item_amount=4800.0, item_rate=4800.0, item_quantity=1.0),
        BillItem(item_name="Sub Total", item_amount=5800.0, item_rate=5800.0, item_quantity=1.0),  # Aggregation
        BillItem(item_name="NICU Charges", item_amount=4800.0, item_rate=4800.0, item_quantity=1.0),  # Duplicate
    ]
    
    print("Original items:", len(items))
    
    # Filter aggregations
    filtered = engine.filter_aggregations(items)
    print(f"After filtering aggregations: {len(filtered)}")
    
    # Deduplicate
    unique = engine.deduplicate_items(filtered)
    print(f"After deduplication: {len(unique)}")
    
    for item in unique:
        print(f"  - {item.item_name}: {item.item_amount}")
    
    # Calculate total
    total = engine.calculate_total(unique)
    print(f"\nTotal: {total}")


if __name__ == "__main__":
    test_deduplication()