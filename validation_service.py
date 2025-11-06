# app/validation_service.py
"""
Validation Service - Complete field validation logic
Handles: text, date, list (simple/hierarchical/multiselect), parent-child, arrays, cross-field, boolean, percentage, textarea
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, InvalidOperation


class ValidationService:
    """Validates extracted fields against template definitions"""
    
    # ===========================
    # REGEX PATTERNS
    # ===========================
    PATTERNS = {
        # Existing patterns
        "aadhaar": r"^\d{12}$",
        "pan": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
        "passport": r"^[A-Z][0-9]{7}$",
        "voter_id": r"^[A-Z]{3}[0-9]{7}[A-Z]?$",
        "driving_license": r"^[A-Z]{2}[0-9]{2}(19|20)[0-9]{2}[0-9]{7}$",
        "mobile": r"^[6-9]\d{9}$",
        "email": r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "pincode": r"^[1-9][0-9]{5}$",
        "account_number": r"^\d{9,18}$",
        "ifsc": r"^[A-Z]{4}0[A-Z0-9]{6}$",
        "card_number": r"^\d{16}$",
        "cvv": r"^\d{3,4}$",
        "upi_id": r"^[a-zA-Z0-9._-]+@[a-zA-Z]+$",
        "gst": r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$",
        "tan": r"^[A-Z]{4}\d{5}[A-Z]{1}$",
        "vehicle_number": r"^[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{1,4}$",
        "blood_group": r"^(A|B|AB|O)[+-]$",
        
        # NEW PATTERNS ADDED
        "registration_number": r"^[A-Z0-9\-\/]{6,20}$",  # Birth/Marriage/Property registration
        "pension_id": r"^[A-Z0-9]{10,15}$",  # Pension ID format
        "policy_number": r"^[A-Z0-9\/\-]{8,20}$",  # Insurance policy number
        "demat_account": r"^IN\d{14}$",  # Demat account (IN + 14 digits)
        "folio_number": r"^[A-Z0-9\/\-]{8,15}$",  # Mutual fund folio number
        "nps_pran": r"^\d{12}$",  # NPS PRAN (12 digits)
        "uan": r"^\d{12}$",  # UAN for EPF (12 digits)
        "license_number": r"^[A-Z0-9\-\/]{8,20}$",  # Professional license number
        "roll_number": r"^[A-Z0-9\-\/]{6,15}$",  # Education roll number
        "cheque_number": r"^\d{6}$",  # Cheque number (6 digits)
    }
    
    # ===========================
    # DATE FORMATS
    # ===========================
    DATE_FORMATS = {
        "dd_mm_yyyy": ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"],
        "mm_dd_yyyy": ["%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y"],
        "yyyy_mm_dd": ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"],
        "dd_mon_yyyy": ["%d %b %Y", "%d %B %Y"],
        "mm_yyyy": ["%m/%Y", "%m-%Y"],
    }
    
    
    def validate_fields(
        self, 
        data: Dict[str, Any], 
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main validation function.
        
        Args:
            data: Field data to validate (from any source: LLM, user input, database, etc.)
            template: Template with field definitions
            
        Returns:
            {
                "valid": bool,
                "normalized_data": {},
                "errors": {},
                "warnings": {},
                "confidence": "high" | "medium" | "low"
            }
        """
        normalized_data = {}
        errors = {}
        warnings = {}
        confidence_scores = []
        
        # First pass: Validate all fields
        for field_def in template.get("fields", []):
            result = self._validate_single_field(field_def, data, template)
            
            field_name = field_def["name"]
            
            if result["valid"]:
                normalized_data[field_name] = result["value"]
                confidence_scores.append(result["confidence"])
                if result.get("warning"):
                    warnings[field_name] = result["warning"]
            else:
                errors[field_name] = result["error"]
                confidence_scores.append(0)
        
        # Second pass: Parent-child validation
        parent_child_errors = self._validate_parent_children(normalized_data, data, template)
        errors.update(parent_child_errors)
        
        # Third pass: Cross-field validation
        cross_field_errors = self._validate_cross_fields(normalized_data, template)
        errors.update(cross_field_errors)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        if avg_confidence >= 0.8:
            confidence_level = "high"
        elif avg_confidence >= 0.5:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        return {
            "valid": len(errors) == 0,
            "normalized_data": normalized_data,
            "errors": errors,
            "warnings": warnings,
            "confidence": confidence_level
        }
    
    
    def _validate_single_field(
        self,
        field_def: Dict[str, Any],
        data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single field based on its definition"""
        
        field_name = field_def["name"]
        field_type = field_def["type"]
        required = field_def.get("required", False)
        
        # Get extracted value
        extracted_value = data.get(field_name)
        
        # Check if required field is missing
        if required and not extracted_value:
            return {
                "valid": False,
                "error": "Required field missing",
                "confidence": 0
            }
        
        # Skip if not extracted and not required
        if not extracted_value:
            return {
                "valid": True,
                "value": None,
                "confidence": 1.0
            }
        
        # Route to appropriate validator based on type
        if field_type == "text":
            return self._validate_text_field(extracted_value, field_def)
        
        elif field_type == "date":
            return self._validate_date_field(extracted_value, field_def)
        
        elif field_type == "list":
            list_type = field_def.get("list_type", "simple")
            if list_type == "simple":
                return self._validate_simple_list(extracted_value, field_def)
            elif list_type == "hierarchical":
                return self._validate_hierarchical_list(extracted_value, field_def, data)
        
        elif field_type == "multiselect":
            return self._validate_multiselect(extracted_value, field_def)
        
        elif field_type == "number":
            return self._validate_number(extracted_value, field_def)
        
        elif field_type == "amount":
            return self._validate_amount(extracted_value, field_def)
        
        elif field_type == "array":
            return self._validate_array(extracted_value, field_def)
        
        elif field_type == "composite":
            return self._validate_composite(extracted_value, field_def, data)
        
        # NEW TYPES ADDED
        elif field_type == "boolean":
            return self._validate_boolean(extracted_value, field_def)
        
        elif field_type == "percentage":
            return self._validate_percentage(extracted_value, field_def)
        
        elif field_type == "textarea":
            return self._validate_textarea(extracted_value, field_def)
        
        else:
            # Unknown type - accept as-is with warning
            return {
                "valid": True,
                "value": extracted_value,
                "confidence": 0.5,
                "warning": f"Unknown field type: {field_type}"
            }
    
    
    # ===========================
    # TEXT FIELD VALIDATION
    # ===========================
    def _validate_text_field(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate text field with optional format"""
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        format_type = field_def.get("format")
        
        # No format - accept any text
        if not format_type:
            return {
                "valid": True,
                "value": value,
                "confidence": 1.0
            }
        
        # Clean value for certain formats
        if format_type in ["aadhaar", "pan", "mobile", "card_number", "driving_license"]:
            cleaned = re.sub(r'[\s\-]', '', value).upper()
        else:
            cleaned = value.upper()
        
        # Validate against pattern
        pattern = self.PATTERNS.get(format_type)
        if not pattern:
            return {
                "valid": True,
                "value": value,
                "confidence": 0.5,
                "warning": f"Unknown format: {format_type}"
            }
        
        if re.match(pattern, cleaned):
            return {
                "valid": True,
                "value": cleaned,
                "confidence": 1.0
            }
        else:
            return {
                "valid": False,
                "error": f"Invalid {format_type} format",
                "confidence": 0
            }
    
    
    # ===========================
    # DATE FIELD VALIDATION
    # ===========================
    def _validate_date_field(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize date to ISO format (YYYY-MM-DD)"""
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        format_type = field_def.get("format", "dd_mm_yyyy")
        
        # Get allowed formats
        format_patterns = self.DATE_FORMATS.get(format_type, ["%d/%m/%Y", "%d-%m-%Y"])
        
        # Try parsing with each format
        for fmt in format_patterns:
            try:
                parsed_date = datetime.strptime(value, fmt)
                iso_date = parsed_date.strftime("%Y-%m-%d")
                return {
                    "valid": True,
                    "value": iso_date,
                    "confidence": 1.0
                }
            except ValueError:
                continue
        
        # Could not parse
        return {
            "valid": False,
            "error": f"Invalid date format. Expected {format_type}",
            "confidence": 0
        }
    
    
    # ===========================
    # LIST VALIDATION (3 TYPES)
    # ===========================
    
    def _validate_simple_list(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate simple list (single selection)"""
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        options = field_def.get("options", [])
        
        if not options:
            return {
                "valid": False,
                "error": "No options defined for list",
                "confidence": 0
            }
        
        # Case-insensitive exact match
        value_lower = value.lower()
        options_lower = [opt.lower() for opt in options]
        
        if value_lower in options_lower:
            idx = options_lower.index(value_lower)
            return {
                "valid": True,
                "value": options[idx],  # Return original casing
                "confidence": 1.0
            }
        
        # Fuzzy match (substring)
        for i, opt in enumerate(options):
            if value_lower in opt.lower() or opt.lower() in value_lower:
                return {
                    "valid": True,
                    "value": options[i],
                    "confidence": 0.8,
                    "warning": f"Fuzzy matched '{value}' to '{options[i]}'"
                }
        
        return {
            "valid": False,
            "error": f"Value must be one of: {', '.join(options)}",
            "confidence": 0
        }
    
    
    def _validate_hierarchical_list(
        self,
        value: Any,
        field_def: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate hierarchical list (parent-child relationship)
        
        Example:
        {
            "name": "location",
            "type": "list",
            "list_type": "hierarchical",
            "parent_field": "state",
            "child_field": "city",
            "allow_parent_without_child": true,
            "options": {
                "Maharashtra": ["Mumbai", "Pune"],
                "Karnataka": ["Bangalore", "Mysore"]
            }
        }
        """
        
        parent_field = field_def.get("parent_field")
        child_field = field_def.get("child_field")
        allow_parent_without_child = field_def.get("allow_parent_without_child", True)
        options = field_def.get("options", {})
        
        field_name = field_def["name"]
        
        # Determine if this is parent or child field
        is_parent = field_name == parent_field
        is_child = field_name == child_field
        
        if is_parent:
            # Validate parent value
            parent_value = str(value).strip()
            
            # Check if parent exists in options
            parent_lower = parent_value.lower()
            options_lower = {k.lower(): k for k in options.keys()}
            
            if parent_lower not in options_lower:
                return {
                    "valid": False,
                    "error": f"Invalid parent value. Must be one of: {', '.join(options.keys())}",
                    "confidence": 0
                }
            
            # Get original casing
            parent_normalized = options_lower[parent_lower]
            
            # Check if child is required
            if not allow_parent_without_child:
                child_value = data.get(child_field)
                if not child_value:
                    return {
                        "valid": False,
                        "error": f"Child field '{child_field}' is required when parent is selected",
                        "confidence": 0
                    }
            
            return {
                "valid": True,
                "value": parent_normalized,
                "confidence": 1.0
            }
        
        elif is_child:
            # Validate child value against parent
            child_value = str(value).strip()
            parent_value = data.get(parent_field)
            
            if not parent_value:
                if allow_parent_without_child:
                    # Parent not selected, child optional
                    return {
                        "valid": True,
                        "value": None,
                        "confidence": 1.0,
                        "warning": "Child value ignored as parent not selected"
                    }
                else:
                    return {
                        "valid": False,
                        "error": "Parent field must be selected first",
                        "confidence": 0
                    }
            
            # Get valid children for this parent
            valid_children = options.get(parent_value, [])
            
            if not valid_children:
                return {
                    "valid": False,
                    "error": f"No valid children defined for parent '{parent_value}'",
                    "confidence": 0
                }
            
            # Case-insensitive match
            child_lower = child_value.lower()
            children_lower = [c.lower() for c in valid_children]
            
            if child_lower in children_lower:
                idx = children_lower.index(child_lower)
                return {
                    "valid": True,
                    "value": valid_children[idx],
                    "confidence": 1.0
                }
            else:
                return {
                    "valid": False,
                    "error": f"Invalid child value. Must be one of: {', '.join(valid_children)}",
                    "confidence": 0
                }
        
        else:
            return {
                "valid": False,
                "error": "Field is neither parent nor child in hierarchical list",
                "confidence": 0
            }
    
    
    def _validate_multiselect(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate multiselect list (array of selections)"""
        
        options = field_def.get("options", [])
        
        # Parse value into list
        if isinstance(value, list):
            values = value
        elif isinstance(value, str):
            # Split by comma, semicolon, pipe
            values = re.split(r'[,;|]', value)
        else:
            values = [str(value)]
        
        # Validate each value
        normalized_values = []
        confidences = []
        warnings = []
        
        for val in values:
            val = val.strip()
            result = self._validate_simple_list(val, {"options": options})
            
            if result["valid"]:
                normalized_values.append(result["value"])
                confidences.append(result["confidence"])
                if result.get("warning"):
                    warnings.append(result["warning"])
            else:
                return {
                    "valid": False,
                    "error": result["error"],
                    "confidence": 0
                }
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "valid": True,
            "value": normalized_values,
            "confidence": avg_confidence,
            "warning": "; ".join(warnings) if warnings else None
        }
    
    
    # ===========================
    # NUMBER & AMOUNT VALIDATION
    # ===========================
    
    def _validate_number(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate number field"""
        
        try:
            if isinstance(value, str):
                # Remove commas, spaces, and percentage signs
                value = value.replace(',', '').replace(' ', '').replace('%', '')
            
            # Try parsing as float first (handles decimals)
            num = float(value)
            
            # If integer required, convert
            if field_def.get("integer_only"):
                num = int(num)
            
            # Check min/max if defined
            min_val = field_def.get("min")
            max_val = field_def.get("max")
            
            if min_val is not None and num < min_val:
                return {
                    "valid": False,
                    "error": f"Value must be >= {min_val}",
                    "confidence": 0
                }
            
            if max_val is not None and num > max_val:
                return {
                    "valid": False,
                    "error": f"Value must be <= {max_val}",
                    "confidence": 0
                }
            
            return {
                "valid": True,
                "value": num,
                "confidence": 1.0
            }
        except (ValueError, TypeError):
            return {
                "valid": False,
                "error": "Invalid number format",
                "confidence": 0
            }
    
    
    def _validate_amount(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate amount/decimal field"""
        
        try:
            if isinstance(value, str):
                value = re.sub(r'[₹$,\s]', '', value)
            
            amount = Decimal(value)
            
            return {
                "valid": True,
                "value": float(amount),  # Convert to float for JSON serialization
                "confidence": 1.0
            }
        except (InvalidOperation, ValueError, TypeError):
            return {
                "valid": False,
                "error": "Invalid amount format",
                "confidence": 0
            }
    
    
    # ===========================
    # NEW: BOOLEAN VALIDATION
    # ===========================
    
    def _validate_boolean(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate boolean field"""
        
        # Handle various boolean representations
        if isinstance(value, bool):
            return {
                "valid": True,
                "value": value,
                "confidence": 1.0
            }
        
        if isinstance(value, str):
            value_lower = value.strip().lower()
            
            # True values
            if value_lower in ["true", "yes", "1", "y", "t"]:
                return {
                    "valid": True,
                    "value": True,
                    "confidence": 1.0
                }
            
            # False values
            if value_lower in ["false", "no", "0", "n", "f"]:
                return {
                    "valid": True,
                    "value": False,
                    "confidence": 1.0
                }
        
        if isinstance(value, int):
            return {
                "valid": True,
                "value": bool(value),
                "confidence": 1.0
            }
        
        return {
            "valid": False,
            "error": "Invalid boolean value. Expected: true/false, yes/no, 1/0",
            "confidence": 0
        }
    
    
    # ===========================
    # NEW: PERCENTAGE VALIDATION
    # ===========================
    
    def _validate_percentage(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate percentage field (0-100 with decimals)"""
        
        try:
            if isinstance(value, str):
                # Remove % symbol if present
                value = value.replace('%', '').replace(' ', '').strip()
            
            # Parse as float
            percent_value = float(value)
            
            # Get min/max (default 0-100)
            min_val = field_def.get("min", 0)
            max_val = field_def.get("max", 100)
            
            # Validate range
            if percent_value < min_val or percent_value > max_val:
                return {
                    "valid": False,
                    "error": f"Percentage must be between {min_val} and {max_val}",
                    "confidence": 0
                }
            
            # Check decimal places if specified
            decimal_places = field_def.get("decimal_places")
            if decimal_places is not None:
                percent_value = round(percent_value, decimal_places)
            
            return {
                "valid": True,
                "value": percent_value,
                "confidence": 1.0
            }
        
        except (ValueError, TypeError):
            return {
                "valid": False,
                "error": "Invalid percentage format",
                "confidence": 0
            }
    
    
    # ===========================
    # NEW: TEXTAREA VALIDATION
    # ===========================
    
    def _validate_textarea(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate textarea field (long text with max length)"""
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Check max length if specified
        max_length = field_def.get("max_length", 5000)  # Default 5000 chars
        
        if len(value) > max_length:
            return {
                "valid": False,
                "error": f"Text exceeds maximum length of {max_length} characters",
                "confidence": 0
            }
        
        # Check min length if specified
        min_length = field_def.get("min_length", 0)
        
        if len(value) < min_length:
            return {
                "valid": False,
                "error": f"Text must be at least {min_length} characters",
                "confidence": 0
            }
        
        return {
            "valid": True,
            "value": value,
            "confidence": 1.0
        }
    
    
    # ===========================
    # ARRAY VALIDATION
    # ===========================
    
    def _validate_array(
        self,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate array of items (repeating fields)
        
        Example:
        {
            "name": "nominees",
            "type": "array",
            "max_items": 5,
            "item_schema": {
                "name": {"type": "text", "required": true},
                "share": {"type": "number", "required": true}
            }
        }
        """
        
        if not isinstance(value, list):
            return {
                "valid": False,
                "error": "Value must be an array",
                "confidence": 0
            }
        
        max_items = field_def.get("max_items")
        item_schema = field_def.get("item_schema", {})
        
        # Check max items
        if max_items and len(value) > max_items:
            return {
                "valid": False,
                "error": f"Maximum {max_items} items allowed",
                "confidence": 0
            }
        
        # Validate each item
        normalized_items = []
        
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                return {
                    "valid": False,
                    "error": f"Item {i+1} must be an object",
                    "confidence": 0
                }
            
            # Validate each field in item
            normalized_item = {}
            
            for field_name, field_def_inner in item_schema.items():
                item_value = item.get(field_name)
                
                # Check required
                if field_def_inner.get("required") and not item_value:
                    return {
                        "valid": False,
                        "error": f"Item {i+1}: field '{field_name}' is required",
                        "confidence": 0
                    }
                
                if item_value:
                    # Validate field
                    result = self._validate_single_field(
                        {**field_def_inner, "name": field_name},
                        item,
                        {}
                    )
                    
                    if not result["valid"]:
                        return {
                            "valid": False,
                            "error": f"Item {i+1}: {result['error']}",
                            "confidence": 0
                        }
                    
                    normalized_item[field_name] = result["value"]
            
            normalized_items.append(normalized_item)
        
        return {
            "valid": True,
            "value": normalized_items,
            "confidence": 1.0
        }
    
    
    # ===========================
    # COMPOSITE FIELD VALIDATION
    # ===========================
    
    def _validate_composite(
        self,
        value: Any,
        field_def: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate composite field (multiple components combined)
        
        Example:
        {
            "name": "full_address",
            "type": "composite",
            "components": [
                {"name": "street", "type": "text"},
                {"name": "city", "type": "text"},
                {"name": "pincode", "type": "text", "format": "pincode"}
            ]
        }
        """
        
        components = field_def.get("components", [])
        composite_value = {}
        has_any_value = False
        
        for component_def in components:
            comp_name = component_def["name"]
            comp_value = data.get(comp_name)
            
            if comp_value:
                has_any_value = True
                # Validate each component
                result = self._validate_single_field(component_def, {comp_name: comp_value}, {})
                
                if not result["valid"]:
                    return {
                        "valid": False,
                        "error": f"Component '{comp_name}': {result['error']}",
                        "confidence": 0
                    }
                
                composite_value[comp_name] = result["value"]
        
        # If no components have values, return null
        if not has_any_value:
            return {
                "valid": True,
                "value": None,
                "confidence": 1.0
            }
        
        return {
            "valid": True,
            "value": composite_value,
            "confidence": 1.0
        }
    
    
    # ===========================
    # PARENT-CHILD VALIDATION
    # ===========================
    
    def _validate_parent_children(
        self,
        normalized_data: Dict[str, Any],
        data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Validate parent-child conditional fields
        
        Example:
        If marital_status = "Married", then spouse_name is required
        """
        
        errors = {}
        
        for field_def in template.get("fields", []):
            children_def = field_def.get("children", {})
            
            if not children_def:
                continue
            
            field_name = field_def["name"]
            parent_value = normalized_data.get(field_name)
            
            if not parent_value:
                continue
            
            # Get children for this parent value
            children_fields = children_def.get(parent_value, [])
            
            for child_field_def in children_fields:
                child_name = child_field_def["name"]
                child_required = child_field_def.get("required", False)
                child_value = data.get(child_name)
                
                # Check if required child is missing
                if child_required and not child_value:
                    errors[child_name] = f"Required field missing (conditional on {field_name}='{parent_value}')"
        
        return errors
    
    
    # ===========================
    # CROSS-FIELD VALIDATION
    # ===========================
    
    def _validate_cross_fields(
        self,
        normalized_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Validate cross-field constraints
        
        Examples:
        - Array sum validation (nominee shares = 100%)
        - Date comparisons (retirement > joining)
        - Parent-child conditionals
        """
        
        errors = {}
        
        for field_def in template.get("fields", []):
            validation_rules = field_def.get("validation", {})
            
            if not validation_rules:
                continue
            
            field_name = field_def["name"]
            field_value = normalized_data.get(field_name)
            
            # Sum validation for arrays
            if "sum_of" in validation_rules:
                sum_field = validation_rules["sum_of"]
                must_equal = validation_rules.get("must_equal")
                
                if isinstance(field_value, list):
                    total = sum(item.get(sum_field, 0) for item in field_value)
                    
                    if must_equal is not None and total != must_equal:
                        errors[field_name] = f"Sum of '{sum_field}' must equal {must_equal}, got {total}"
            
            # Date comparison
            if "must_be_after" in validation_rules:
                after_field = validation_rules["must_be_after"]
                after_value = normalized_data.get(after_field)
                
                if field_value and after_value:
                    try:
                        date1 = datetime.strptime(field_value, "%Y-%m-%d")
                        date2 = datetime.strptime(after_value, "%Y-%m-%d")
                        
                        if date1 <= date2:
                            errors[field_name] = f"Must be after '{after_field}'"
                    except ValueError:
                        pass
        
        return errors