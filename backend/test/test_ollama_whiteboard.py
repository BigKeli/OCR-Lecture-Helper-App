#!/usr/bin/env python3
"""
Test script for Ollama Vision with real whiteboard image
Tests different tasks: read, describe, summarize, and custom prompt
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.ollama_client import ollama_client
from flask import Flask
import cv2

# Create a test Flask app for config
app = Flask(__name__)
app.config['OLLAMA_BASE_URL'] = 'https://ai.integriert-studieren.jku.at'
app.config['OLLAMA_USERNAME'] = 'kvat'
app.config['OLLAMA_PASSWORD'] = 'kvat123pw'
app.config['OLLAMA_DEFAULT_MODEL'] = 'gemma3:4b'
app.config['OLLAMA_NUM_PREDICT'] = 2600
app.config['OLLAMA_TEMPERATURE'] = 0.7

# ANSI color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
MAGENTA = "\033[95m"

def load_whiteboard_image():
    """Load the whiteboard image"""
    image_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'scripts', 'output', '00_original.png'
    )
    
    if not os.path.exists(image_path):
        print(f"{RED}❌ Image not found: {image_path}{RESET}")
        return None
    
    print(f"{GREEN}✓ Loading image: {image_path}{RESET}")
    frame = cv2.imread(image_path)
    
    if frame is None:
        print(f"{RED}❌ Failed to load image{RESET}")
        return None
    
    print(f"{GREEN}✓ Image loaded successfully: {frame.shape}{RESET}")
    return frame

def test_task(frame, task_name, prompt, model='gemma3:4b'):
    """Test a specific task with Ollama"""
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{MAGENTA}TEST: {task_name.upper()}{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{YELLOW}Model:{RESET} {model}")
    print(f"{YELLOW}Prompt:{RESET} {prompt}")
    print()
    
    start_time = time.time()
    
    print(f"{CYAN}🔄 Sending request to Ollama API...{RESET}")
    
    result = ollama_client.generate_vision(
        frame=frame,
        prompt=prompt,
        model=model,
        num_predict=2600,
        temperature=0.7
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n{BOLD}{'─'*80}{RESET}")
    print(f"{BOLD}RESULT{RESET}")
    print(f"{BOLD}{'─'*80}{RESET}\n")
    
    if result['success']:
        print(f"{GREEN}✅ Success!{RESET}")
        print(f"{YELLOW}Provider:{RESET} {result.get('provider', 'unknown')}")
        print(f"{YELLOW}Model:{RESET} {result.get('model', 'unknown')}")
        print(f"{YELLOW}Time:{RESET} {elapsed:.2f}s")
        
        # Show performance metrics if available
        if result.get('eval_count'):
            print(f"{YELLOW}Tokens:{RESET} {result['eval_count']}")
        
        print(f"\n{BOLD}Response:{RESET}")
        print(f"{CYAN}{'─'*80}{RESET}")
        print(result['text'])
        print(f"{CYAN}{'─'*80}{RESET}")
        
        return True
    else:
        print(f"{RED}❌ Error: {result.get('error', 'Unknown error')}{RESET}")
        return False

def run_all_tests():
    """Run all tests sequentially"""
    with app.app_context():
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}🧪 JKU OLLAMA VISION - WHITEBOARD TESTING SUITE{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")
        
        # Load the whiteboard image
        print(f"{BOLD}📸 Loading whiteboard image...{RESET}")
        frame = load_whiteboard_image()
        
        if frame is None:
            print(f"{RED}❌ Failed to load image. Exiting.{RESET}")
            return False
        
        print(f"{GREEN}✓ Image ready for testing{RESET}")
        
        # Define test cases
        tests = [
            {
                'name': 'Read Text',
                'prompt': 'Read all the text visible on this slide or board clearly and accurately. Include all text content.'
            },
            {
                'name': 'Describe',
                'prompt': 'Describe what you see on this slide or board, focusing on the main content and any diagrams.'
            },
            {
                'name': 'Summarize',
                'prompt': 'Summarize the key points shown on this slide or board in 2-3 concise bullet points.'
            },
            {
                'name': 'Custom - Explain Concepts',
                'prompt': 'Explain the main concepts or ideas presented in this image. If there are any mathematical formulas, equations, or diagrams, explain what they represent and their significance.'
            }
        ]
        
        # Run tests sequentially
        results = []
        for i, test in enumerate(tests, 1):
            print(f"\n{BOLD}{YELLOW}[{i}/{len(tests)}] Running test...{RESET}")
            success = test_task(frame, test['name'], test['prompt'])
            results.append(success)
            
            # Wait a bit between tests to avoid rate limiting
            if i < len(tests):
                print(f"\n{YELLOW}⏳ Waiting 2 seconds before next test...{RESET}")
                time.sleep(2)
        
        # Summary
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}📊 TEST SUMMARY{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")
        
        passed = sum(results)
        total = len(results)
        
        for i, (test, result) in enumerate(zip(tests, results), 1):
            status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
            print(f"{i}. {test['name']}: {status}")
        
        print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}")
        
        if passed == total:
            print(f"\n{GREEN}{BOLD}🎉 All tests passed!{RESET}")
            return True
        else:
            print(f"\n{RED}{BOLD}⚠️  Some tests failed{RESET}")
            return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Tests interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}❌ Exception: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
