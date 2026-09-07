"""
Helper functions - Updated with exact number formatting
"""

def format_number(num, format_type='exact'):
    """
    Format numbers for display
    
    Args:
        num: Number to format
        format_type: 'exact' (24,300), 'compact' (24.3K), 'indian' (24,300)
    """
    try:
        if num is None:
            return "0"
        
        num = float(num)
        
        if format_type == 'exact':
            # Indian number format: 24,300 or 2,45,000
            return f"{num:,.0f}"
        
        elif format_type == 'indian':
            # Indian format with commas: 1,00,000
            num_str = str(int(num))
            if len(num_str) <= 3:
                return num_str
            last_three = num_str[-3:]
            rest = num_str[:-3]
            # Add commas in Indian format
            rest_with_commas = ''
            while len(rest) > 2:
                rest_with_commas = ',' + rest[-2:] + rest_with_commas
                rest = rest[:-2]
            if rest:
                rest_with_commas = rest + rest_with_commas
            return rest_with_commas + ',' + last_three
        
        elif format_type == 'compact':
            if abs(num) >= 10000000:
                return f"{num/10000000:.2f}Cr"
            elif abs(num) >= 100000:
                return f"{num/100000:.2f}L"
            elif abs(num) >= 1000:
                return f"{num/1000:.2f}K"
            else:
                return f"{num:.0f}"
        
        else:
            return f"{num:,.2f}"
            
    except:
        return "0"


def format_currency(num):
    """Format as currency"""
    try:
        return f"₹{float(num):,.2f}"
    except:
        return "₹0.00"


def format_exact(num):
    """Exact number with Indian format"""
    try:
        num = int(float(num))
        return f"{num:,}"
    except:
        return "0"