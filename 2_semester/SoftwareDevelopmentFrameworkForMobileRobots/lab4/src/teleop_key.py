import pygame
import time
import argparse
import os

os.environ['CYCLONEDDS_INTERFACE'] = 'lo0'

from dds_interface import DDSInterface
from dds_models import Twist


class TeleopKey:
    def __init__(self, turtle_name: str = "turtle1"):
        pygame.init()
        self.turtle_name = turtle_name

        self.screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption(f"Teleop: {turtle_name}")
        self.font = pygame.font.Font(None, 24)

        self.dds = DDSInterface()

        topic_name = f"/{turtle_name}/cmd_vel"
        self.cmd_pub = self.dds.create_publisher(topic_name, Twist)

        self.linear_vel = 0.0
        self.angular_vel = 0.0

        self.max_linear = 2.0
        self.max_angular = 1.5
        self.linear_step = 0.3
        self.angular_step = 0.1


    def run(self):
        clock = pygame.time.Clock()
        running = True
        publish_count = 0
        last_publish = time.time()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            keys = pygame.key.get_pressed()

            if keys[pygame.K_UP]:
                self.linear_vel += self.linear_step
                if self.linear_vel > self.max_linear:
                    self.linear_vel = self.max_linear

            elif keys[pygame.K_DOWN]:
                self.linear_vel -= self.linear_step
                if self.linear_vel < -self.max_linear:
                    self.linear_vel = -self.max_linear

            else:
                self.linear_vel *= 0.98

            if keys[pygame.K_LEFT]:
                self.angular_vel += self.angular_step
                if self.angular_vel > self.max_angular:
                    self.angular_vel = self.max_angular

            elif keys[pygame.K_RIGHT]:
                self.angular_vel -= self.angular_step
                if self.angular_vel < -self.max_angular:
                    self.angular_vel = -self.max_angular

            else:
                self.angular_vel *= 0.78


            if abs(self.linear_vel) < 0.01:
                self.linear_vel = 0.0
            if abs(self.angular_vel) < 0.01:
                self.angular_vel = 0.0


            twist = Twist()
            twist.linear_x = self.linear_vel
            twist.linear_y = 0.0
            twist.linear_z = 0.0
            twist.angular_x = 0.0
            twist.angular_y = 0.0
            twist.angular_z = self.angular_vel

            now = time.time()
            if now - last_publish >= 0.05:
                self.dds.publish(self.cmd_pub, twist)
                publish_count += 1

                last_publish = now

            self.screen.fill((50, 50, 50))

            title = self.font.render(f"Teleop: {self.turtle_name}", True, (0, 255, 0))
            self.screen.blit(title, (10, 10))

            linear_text = self.font.render(f"linear_x: {self.linear_vel:.2f}", True, (255, 255, 255))
            angular_text = self.font.render(f"angular_z: {self.angular_vel:.2f}", True, (255, 255, 255))
            self.screen.blit(linear_text, (10, 50))
            self.screen.blit(angular_text, (10, 80))

            count_text = self.font.render(f"sent: {publish_count}", True, (200, 200, 200))
            self.screen.blit(count_text, (10, 120))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--turtle', default='turtle1', help='Имя черепашки')
    args = parser.parse_args()

    teleop = TeleopKey(args.turtle)
    teleop.run()


if __name__ == '__main__':
    main()