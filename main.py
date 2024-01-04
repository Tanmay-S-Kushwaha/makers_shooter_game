import pygame
import random
import os
import csv
import button
from pygame import mixer
import time

pygame.init()
mixer.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.6
SCROLL_THRESH = 200
TILE_SIZE= 40
ROWS=16
COLS=150
TILE_SIZE = SCREEN_HEIGHT//ROWS
TILE_TYPES = 21
MAX_LEVELS =3
screen_scroll = 0
bg_scroll = 0
level=1
start_game=False

#define player action variables
moving_left = False
moving_right = False
shoot = False
grenade= False
grenade_thrown = False
#music
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1,0.0,5000)
jump_fx=pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
shot_fx=pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)
grenade_fx=pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)
#load images
pine1_img = pygame.image.load('img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky_cloud.png').convert_alpha()
#button
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#tiles
img_list=[]
for x in range(TILE_TYPES):
	img=pygame.image.load(f'img/Tile/{x}.png')
	img=pygame.transform.scale(img,(TILE_SIZE,TILE_SIZE))
	img_list.append(img)
#bullet
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()

health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes ={
	'Health':health_box_img ,
	'Ammo':ammo_box_img,
	'Grenade':grenade_box_img 
}



#define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
GREEN = (0,255,0)

#font
font= pygame.font.SysFont('Futura',30)

def draw_text(text,font,text_col,x,y):
	img  =font.render(text, True, text_col)
	screen.blit(img,(x,y))
	
def draw_bg():
	screen.fill(BG)
	width=sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img,((x*width)-bg_scroll*.5,0))
		screen.blit(mountain_img,((x*width)-bg_scroll*.6,SCREEN_HEIGHT-mountain_img.get_height()-300))
		screen.blit(pine1_img,((x*width)-bg_scroll*.7,SCREEN_HEIGHT-pine1_img.get_height()-150))
		screen.blit(pine2_img,((x*width)-bg_scroll*.8,SCREEN_HEIGHT-pine2_img.get_height()))

def reset_level():
	bullet_group.empty()
		
	grenade_group.empty()
		
	explosion_group.empty()		
	item_box_group.empty()
		
	decoration_group.empty()
		
	exit_group.empty()
		
	water_group.empty()
	#create empty tile list
	data = []


	r=[]
	for i in range(ROWS):
		data.append([-1]*COLS)
	return data
		
class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo,grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		self.grenades=grenades
		#ai specific
		self.idling=False
		self.idling_counter=0
		self.move_counter=0
		self.vision = pygame.Rect(0,0,150,20)
		

		
		#load all images for the players
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#reset temporary list of images
			temp_list = []
			#count number of files in the folder
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width=self.image.get_width()
		self.height=self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()
		if self.char_type == 'enemy':
			self.ai()
		#update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1


	def move(self, moving_left, moving_right):
		screen_scroll=0
		#reset movement variables
		dx = 0
		dy = 0

		#assign movement variables if moving left or right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		#apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		#check collision 
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect.x+dx,self.rect.y,self.width,self.height):
				dx=0
			if tile[1].colliderect(self.rect.x,self.rect.y+dy,self.width,self.height):
				#check for below
				if self.vel_y <0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check for above 
				elif self.vel_y >=0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom

		if pygame.sprite.spritecollide(self,water_group,False):
					self.health = 0
		level_complete=False
		if pygame.sprite.spritecollide(self,exit_group,False):
					level_complete = True
		if self.rect.bottom>SCREEN_HEIGHT:
					self.health=0	
		#going off the screen
					if self.char_type=='player':
						if self.rect.left+dx<0 or self.right +dx> SCREEN_WIDTH:
							dx=0
		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy
		#update_scroll
		if self.char_type=='player':
			if (self.rect.right>SCREEN_WIDTH-SCROLL_THRESH and bg_scroll<(world.level_length*TILE_SIZE)-SCREEN_WIDTH) \
				or (self.rect.left < SCROLL_THRESH and bg_scroll>abs(dx)):
				self.rect.x -=dx
				screen_scroll = -dx
		return screen_scroll,level_complete


	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			#reduce ammo
			self.ammo -= 1
			shot_fx.play()


	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 100
		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#if the animation has run out the reset back to the start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def ai(self):
		if self.alive and player.alive:
			if random.randint(1,200)==1 and self.idling==False:
				self.idling=True
				self.idling_counter=50
				self.update_action(0)
			#fire_check
			if self.vision.colliderect(player.rect):
				self.update_action(0)
				self.shoot()
			else:
				if self.idling ==False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left,ai_moving_right)
					self.update_action(1) #run
					self.move_counter +=1
					#update vision
					self.vision.center = (self.rect.centerx+ 75 *self.direction,self.rect.centery)
					#pygame.draw.rect(screen,RED,self.vision)
					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter*=-1
				else:
					self.idling_counter-=1
					if self.idling_counter<=0:
						self.idling=False

		#scroll
		self.rect.x += screen_scroll

			
			
		
	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
		#pygame.draw.rect(screen,'red',self.rect,2)

class World():
	def __init__(self):
		self.obstacle_list=[]
	def process_data(self,data):
		self.level_length = len(data[0])
		#iterate each value in level file
		for y,row in enumerate(data):
			for x,tile in enumerate(row):
				if tile >=0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x*TILE_SIZE
					img_rect.y = y*TILE_SIZE
					tile_data = (img,img_rect)
					if tile >=0 and tile<=8:
						self.obstacle_list.append(tile_data)
					elif tile >=9 and tile<=10:
						water=Water(img,x*TILE_SIZE,y*TILE_SIZE)
						water_group.add(water)#water
					elif tile >=11 and tile<=14:
						#decor
						decoration=Decoration(img,x*TILE_SIZE,y*TILE_SIZE)
						decoration_group.add(decoration)
					elif tile==15:
						#player
						player = Soldier('player', x*TILE_SIZE,y*TILE_SIZE,1.65, 5, 20,5)
						health_bar=HealthBar(10,10,player.health,player.health)
					elif tile==16:
						enemy=Soldier('enemy',x*TILE_SIZE,y*TILE_SIZE,1.65, 2, 20,0)
						enemy_group.add(enemy)
					elif tile==17:#ammobox
						item_box=ItemBox("Ammo",x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==18:#grenade
						item_box=ItemBox("Grenade",x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==19:#health
						item_box=ItemBox("Health",x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==20:
						exit=Exit(img,x*TILE_SIZE,y*TILE_SIZE)
						exit_group.add(exit) #exit
		return player, health_bar
	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] +=screen_scroll
			screen.blit(tile[0],tile[1])

class Decoration(pygame.sprite.Sprite):
	def __init__(self,img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x+TILE_SIZE//2,y+(TILE_SIZE-self.image.get_height()))
	def update(self):
		self.rect.x +=screen_scroll
class Water(pygame.sprite.Sprite):
	def __init__(self,img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x+TILE_SIZE//2,y+(TILE_SIZE-self.image.get_height()))
	def update(self):
		self.rect.x +=screen_scroll
class Exit(pygame.sprite.Sprite):
	def __init__(self,img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x+TILE_SIZE//2,y+(TILE_SIZE-self.image.get_height()))
	def update(self):
		self.rect.x +=screen_scroll
class ItemBox(pygame.sprite.Sprite):
	def __init__(self,item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE//2), y+(TILE_SIZE - self.image.get_height())
	def update(self):
		self.rect.x +=screen_scroll
		if pygame.sprite.collide_rect(self,player):
			#check box type
			if self.item_type =="Health":
				player.health +=25
				if player.health> player.max_health:
					player.health=player.max_health
			elif self.item_type == 'Ammo':
				player.ammo +=15
			elif self.item_type == 'Grenade':
				player.grenades+=3
			#self.kill
			self.kill()

class HealthBar():
	def __init__(self,x,y,health,max_health):
		self.x=x
		self.y=y
		self.health=health
		self.max_health=max_health
	def draw(self,health):
		self.health=health
		pygame.draw.rect(screen,'black',(self.x-2,self.y-2,150+4,20+4) )
		pygame.draw.rect(screen,RED,(self.x,self.y,150,20))
		pygame.draw.rect(screen,GREEN,(self.x,self.y,150*health/self.max_health,20))
		



class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		self.rect.x +=screen_scroll
		#move bullet
		self.rect.x += (self.direction * self.speed)
		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()

		#check collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()
			
		#check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()
				
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer=100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width=self.image.get_width()
		self.height=self.image.get_height()
		self.direction = direction
	def update(self):
		self.rect.x +=screen_scroll
		self.vel_y +=GRAVITY
		dx= self.speed*self.direction
		dy= self.vel_y
		#update pos

		#check for collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect.x+dx,self.rect.y,self.width,self.height):
				self.direction*=-1
				dx=self.direction*self.speed
			if tile[1].colliderect(self.rect.x,self.rect.y+dy,self.width,self.height):
					#check for thrown up
					self.speed=0
					if self.vel_y <0:
						self.vel_y = 0
						dy = tile[1].bottom - self.rect.top
					#check for above , falling
					elif self.vel_y >=0:
						self.vel_y = 0
						dy = tile[1].top - self.rect.bottom
		#check if bullet has gone off screen
		if self.rect.right +dx< 0 or self.rect.left +dx > SCREEN_WIDTH:
			self.direction*= -1
			dx= self.speed*self.direction
		self.rect.x+=dx
		self.rect.y+=dy
		self.timer -= 1
		if self.timer <=0:
			self.kill()
			grenade_fx.play()
			explosion=Explosion(self.rect.x,self.rect.y,self.direction,0.5)
			explosion_group.add(explosion)
			#check for damage
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE *2 and \
			abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE *2 and \
                abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 50
			
		
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, direction,scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img,(int(img.get_width()* scale), int(img.get_height()*scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0
	def update(self):
		EXPLOSION_SPEED = 4
		self.counter+=1
		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index +=1
			#finifsh
			if self.frame_index >= len(self.images):
				self.kill()
			else:   self.image = self.images[self.frame_index]
				
#create buttons
start_button=button.Button(SCREEN_WIDTH//2 -130,SCREEN_HEIGHT//2 -150,start_img,1)
exit_button=button.Button(SCREEN_WIDTH//2 -110,SCREEN_HEIGHT//2 +50,exit_img,1)
restart_button=button.Button(SCREEN_WIDTH//2 -100,SCREEN_HEIGHT//2 -50,restart_img,2)
#create sprite groups
bullet_group = pygame.sprite.Group()
grenade_group=pygame.sprite.Group()
explosion_group=pygame.sprite.Group()
enemy_group=pygame.sprite.Group()
item_box_group=pygame.sprite.Group()
water_group=pygame.sprite.Group()
exit_group=pygame.sprite.Group()
decoration_group=pygame.sprite.Group()

#create	tile list
			
world_data = []


r=[]
for i in range(ROWS):
	world_data.append([-1]*COLS)
#load world data
with open(f'level{level}_data.csv',newline='') as csvfile:
	reader = csv.reader(csvfile,delimiter=',')
	for x,row in enumerate(reader):
		for y,tile in enumerate(row):
			world_data[x][y] = int(tile)

world=World()
player, health_bar = world.process_data(world_data)




#temp - 





run = True
while run:

	clock.tick(FPS)

	if start_game == False:
		#menu
		screen.fill(BG)
		if start_button.draw(screen):
			start_game = True
		if exit_button.draw(screen):
			run = False
		
	else:
		draw_bg()
		world.draw()
		#player health
		health_bar.draw(player.health)

		draw_text('AMMO:',font,'yellow',10,35)
		for x in range(player.ammo):
			screen.blit(bullet_img,(90+(x*10),40))
		draw_text('GRENADE:',font,'yellow',10,60)
		for x in range(player.grenades):
			screen.blit(grenade_img,(125+(x*10),61))
		#draw_text('HEALTH:',font,'yellow',0,120)

		player.update()
		player.draw()
		for enemy in enemy_group:
			enemy.update()
			enemy.draw()

		#update and draw groups
		bullet_group.update()
		bullet_group.draw(screen)
		grenade_group.update()
		grenade_group.draw(screen)
		explosion_group.update()
		explosion_group.draw(screen)
		item_box_group.update()
		item_box_group.draw(screen)
		decoration_group.update()
		decoration_group.draw(screen)
		exit_group.update()
		exit_group.draw(screen)
		water_group.update()
		water_group.draw(screen)
		


		#update player actions
		if player.alive:
			#shoot bullets
			if shoot:
				player.shoot()
			elif grenade and grenade_thrown == False and player.grenades>0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0]*player.direction),\
						player.rect.top, player.direction)
				grenade_group.add(grenade)
				grenade_thrown=True
				player.grenades-=1
			if player.in_air:
				player.update_action(2)#2: jump
			elif moving_left or moving_right:
				player.update_action(1)#1: run
			else:
				player.update_action(0)#0: idle
			screen_scroll, level_complete=player.move(moving_left, moving_right)
			bg_scroll -=screen_scroll
			#check for complate
			if level_complete:
				level+=1
				bg_scroll=0
				world_data = reset_level()
				if level <=MAX_LEVELS:
					with open(f'level{level}_data.csv',newline='') as csvfile:
						reader = csv.reader(csvfile,delimiter=',')
						for x,row in enumerate(reader):
							for y,tile in enumerate(row):
								world_data[x][y] = int(tile)
				else:
					debug_surf = font.render('YOU WON',True,'White')
					debug_rect = debug_surf.get_rect(topleft = (x,y))
					pygame.draw.rect(screen,'white',debug_rect)
					
					screen.fill('black')
					screen.blit(debug_surf,debug_rect)



					world=World()
					player, health_bar = world.process_data(world_data)
		else:
			screen_scroll  = 0
			if restart_button.draw(screen):
				bg_scroll = 0
				world_data=reset_level()
				with open(f'level{level}_data.csv',newline='') as csvfile:
					reader = csv.reader(csvfile,delimiter=',')
					for x,row in enumerate(reader):
						for y,tile in enumerate(row):
							world_data[x][y] = int(tile)

					world=World()
					player, health_bar = world.process_data(world_data)


	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False
		#keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False


		#keyboard button released
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown=False




	pygame.display.update()

pygame.quit()
