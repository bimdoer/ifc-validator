import pytest
import ifcopenshell
from src.validator import IFCValidator
from src.validator.rules import BaseRule


class MockRule(BaseRule):
    """Mock-Regel für Tests."""
    
    def __init__(self, should_fail=False):
        super().__init__("MockRule", "Test rule")
        self.should_fail = should_fail
    
    def validate(self, ifc_file):
        if self.should_fail:
            return [self.create_result(None, "Test error")]
        return []


def test_validator_with_mock_rule():
    """Testet den Validator mit einer Mock-Regel."""
    rule = MockRule(should_fail=False)
    validator = IFCValidator(rules=[rule])
    
    # Erstelle eine minimale IFC-Datei für Tests
    ifc_file = ifcopenshell.file()
    project = ifc_file.createIfcProject()
    
    report = validator.validate(ifc_file)
    assert report.is_valid()


def test_validator_with_failing_rule():
    """Testet den Validator mit einer fehlschlagenden Regel."""
    rule = MockRule(should_fail=True)
    validator = IFCValidator(rules=[rule])
    
    ifc_file = ifcopenshell.file()
    project = ifc_file.createIfcProject()
    
    report = validator.validate(ifc_file)
    assert not report.is_valid()
    assert len(report.get_errors()) == 1

