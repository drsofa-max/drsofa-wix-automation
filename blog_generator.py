import openai
import os
from datetime import datetime

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_blog_post(site_name, city, state, topic, tone, length, custom_keyword=None):
    """
    Generate SEO-optimized blog post using OpenAI GPT-4
    
    Returns:
    {
        'title': str,
        'meta_description': str,
        'body': str
    }
    """
    
    topic_labels = {
        'disassembly': 'sofa disassembly and moving tips',
        'reassembly': 'furniture reassembly after a move',
        'reupholstery': 'sofa reupholstery and fabric options',
        'tips': 'furniture care and maintenance tips',
        'local': 'local moving guide with furniture tips',
        'custom': custom_keyword or 'furniture services'
    }
    
    tone_labels = {
        'helpful': 'helpful and practical',
        'expert': 'authoritative and expert',
        'local': 'friendly and locally focused'
    }
    
    length_labels = {
        'short': '300 words',
        'medium': '600 words',
        'long': '1000 words'
    }
    
    topic_text = topic_labels.get(topic, 'furniture services')
    tone_text = tone_labels.get(tone, 'helpful and practical')
    length_text = length_labels.get(length, '600 words')
    
    prompt = f"""Write a complete SEO-optimized blog post for a furniture disassembly, reassembly, and reupholstery service.

Company: {site_name}
Location: {city}, {state}
Topic: {topic_text}
Tone: {tone_text}
Target length: approximately {length_text}

Requirements:
- Start with META: [155-character SEO meta description]
- Include H1 title with city name
- 2-3 H2 subheadings
- Natural local keywords ({city} + "sofa disassembly", "furniture moving", etc.)
- End with clear CTA to call or chat for quote
- Do NOT use placeholder brackets
- Format exactly:

META: [description here]

# [H1 Title]

[body with ## subheadings]

Write the complete post now:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an SEO-expert copywriter for furniture services."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        full_text = response.choices[0].message.content
        
        # Parse META and body
        lines = full_text.split('\n')
        meta_desc = ''
        body_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith('META:'):
                meta_desc = line.replace('META:', '').strip()
            elif line.startswith('#') and not line.startswith('##'):
                body_start = i
                break
        
        title_line = lines[body_start] if body_start < len(lines) else '# Post'
        title = title_line.replace('#', '').strip()
        
        body = '\n'.join(lines[body_start+1:]).strip()
        
        return {
            'success': True,
            'title': title,
            'meta_description': meta_desc[:160],  # Ensure 160 chars max
            'body': body
        }
        
    except openai.error.RateLimitError:
        return {
            'success': False,
            'error': 'OpenAI rate limit hit. Try again in a moment.'
        }
    except openai.error.AuthenticationError:
        return {
            'success': False,
            'error': 'OpenAI API key invalid. Check OPENAI_API_KEY environment variable.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating post: {str(e)}'
        }
