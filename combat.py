import pygame
import sys
from main import spiller
from main import fiende

pygame.init()

def combat(objekt,fiende):
    krig = objekt.colliderect(fiende)
    

pygame.quit()
sys.exit()