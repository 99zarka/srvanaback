from django.core.management.base import BaseCommand
from ai.rag_system import AIAssistantRAG

class Command(BaseCommand):
    help = 'Rebuild AI Assistant embeddings index'
    
    def handle(self, *args, **options):
        self.stdout.write('Building AI Assistant RAG index...')
        rag = AIAssistantRAG(db_alias='long_running')
        rag.build_index()
        self.stdout.write(
            self.style.SUCCESS('Successfully rebuilt AI index')
        )
