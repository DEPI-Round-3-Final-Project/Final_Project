import re
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib.pyplot as plt
from datetime import datetime

def format_arabic_text(text):
    """تنسيق النص العربي للعرض الصحيح"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def extract_keywords(text, num_keywords=5):
    """Extract keywords from the text"""
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # Split text into words
    words = text.split()
    
    # Remove short words
    words = [word for word in words if len(word) > 3]
    
    # Calculate word frequency
    word_freq = {}
    for word in words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    
    # Sort words by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return the most frequent words
    return [word[0] for word in sorted_words[:num_keywords]]

def is_valid_date(date_string):
    """Check the validity of the date"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def calculate_progress(completed_tasks, total_tasks):
    """Calculate the progress percentage"""
    if total_tasks == 0:
        return 0
    return (completed_tasks / total_tasks) * 100

def generate_study_plan(subjects, days_before_exam):
    """Generate a study plan"""
    plan = {}
    
    # Divide days among subjects
    days_per_subject = days_before_exam // len(subjects)
    
    for subject in subjects:
        plan[subject] = days_per_subject
    
    # Distribute remaining days
    remaining_days = days_before_exam % len(subjects)
    for i in range(remaining_days):
        plan[subjects[i]] += 1
    
    return plan
