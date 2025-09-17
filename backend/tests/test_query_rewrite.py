"""Unit tests for query rewriting module."""
import os
from lexa_app.query_rewrite import expand_query, get_query_intent, is_enabled

class TestQueryRewrite:
    
    def setup_method(self):
        """Reset environment for each test."""
        os.environ.pop("LEXA_USE_QUERY_REWRITE", None)
    
    def test_disabled_by_default(self):
        """Query rewriting should be disabled by default."""
        assert not is_enabled()
        result = expand_query("convert quote to SO")
        assert result == ["convert quote to SO"]
    
    def test_enabled_via_env(self):
        """Query rewriting should activate via environment flag."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        assert is_enabled()
    
    def test_abbreviation_expansion(self):
        """Should expand NetSuite abbreviations."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("convert quote to SO")
        assert "convert quote to sales order" in result
        assert len(result) > 1
    
    def test_synonym_expansion(self):
        """Should expand domain synonyms."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("create customer record")
        assert any("client" in variant for variant in result)
        assert len(result) > 1
    
    def test_process_chain_detection(self):
        """Should detect and expand process chains."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("quote to sale process")
        assert any("convert quote to sales order" in variant for variant in result)
        assert len(result) > 2
    
    def test_procedural_context_addition(self):
        """Should add procedural context to how-to queries."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("how to cancel order")
        assert any("process for cancel order" in variant for variant in result)
        assert any("procedure" in variant for variant in result)
    
    def test_variant_deduplication(self):
        """Should remove duplicate variants."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("SO sales order")  # Should dedupe
        assert len(result) == len(set(result))  # No duplicates
    
    def test_variant_limit(self):
        """Should limit number of variants to prevent explosion."""
        os.environ["LEXA_USE_QUERY_REWRITE"] = "1"
        result = expand_query("how to create customer quote SO")
        assert len(result) <= 5
    
    def test_intent_classification_procedural(self):
        """Should classify procedural queries correctly."""
        assert get_query_intent("how to create sales order") == "procedural"
        assert get_query_intent("steps to convert quote") == "procedural" 
        assert get_query_intent("cancel order process") == "procedural"
    
    def test_intent_classification_troubleshooting(self):
        """Should classify troubleshooting queries correctly."""
        assert get_query_intent("sales order error message") == "troubleshooting"
        assert get_query_intent("quote not working") == "troubleshooting"
        assert get_query_intent("how to fix payment issue") == "troubleshooting"
    
    def test_intent_classification_navigation(self):
        """Should classify navigation queries correctly."""
        assert get_query_intent("where is sales order button") == "navigation"
        assert get_query_intent("where do I find customer page") == "navigation"
        assert get_query_intent("locate quote menu") == "navigation"
    
    def test_intent_classification_factual(self):
        """Should default to factual for other queries."""
        assert get_query_intent("what is NetSuite") == "factual"
        assert get_query_intent("sales order definition") == "factual"