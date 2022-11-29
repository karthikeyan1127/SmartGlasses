from google.cloud import speech_v1 as speech
import speech_recognition as s_r
from google.cloud import vision
import io
import cv2
from gtts import gTTS
import pygame
import pygame.mixer, pygame.time
from io import BytesIO


class SmartVisual:
    read_text_commands = ["read", "reads", "text", "textbook", "voice", "voice out", "book"]
    emotion_commands = ["greet", "hello", "hi", "how are you"]
    possible_emotion = ["POSSIBLE", "LIKELY", "VERY_LIKELY"]
    object_commands = ["whats before me", "visualize", "identify", "before me", "infront of me", "see"]
    remember_commands = ["where is", "where is my", "where"]
    exit_commands = ["thank you", "service not needed", "exit", "shutdown", "close", "sleep"]
    say_again_commands = ["repeat again", "again", "repeat", "say again", "not clear", "not understood"]
    memory = []
    last_read_text = []

    def get_command(self):
        speechRecognizer = s_r.Recognizer()
        speechRecognizer.energy_threshold = 500
        mic = s_r.Microphone(device_index=1)
        # mic = s_r.Microphone(device_index=10)
        with mic as source:
            speechRecognizer.adjust_for_ambient_noise(source)
            print("Say your Command!!!!")
            audio = speechRecognizer.listen(source)
            # audio = speechRecognizer.record(source, duration=10)
        try:
            command = speechRecognizer.recognize_google(audio)
        except Exception as e:
            print(e)
            return
        print(command)
        for match_command in self.read_text_commands:
            if (match_command in command):
                self.detect_text(self.captureImage())
                return
        for match_command in self.emotion_commands:
            if (match_command in command):
                self.detect_emotion(self.captureImage())
                return
        for match_command in self.object_commands:
            if (match_command in command):
                self.detect_objects(self.captureImage())
                return
        for match_command in self.exit_commands:
            if (match_command in command):
                self.speak("Happy to serve you")
                exit(0)
        for match_command in self.say_again_commands:
            if (match_command in command):
                for text in self.last_read_text:
                    self.speak(text)
                return
        for match_command in self.remember_commands:
            if (match_command in command):
                self.track_object(match_command)
                return

    def track_object(self, command):
        for findObj in command:
            for thing in self.memory:
                if findObj in thing:
                    thing.replace(findObj, "")
                    self.speak(findObj + " found near " + thing)
                    return

    def speak(self, text):
        audio_format = BytesIO()
        speak_out = gTTS(text, lang='en')
        speak_out.write_to_fp(audio_format)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(audio_format, 'mp3')
        channel = pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue

        print("Finished.")

    def captureImage(self):
        capture = cv2.VideoCapture(0)
        ret, frame = capture.read()
        cv2.imshow("frame", frame)
        cv2.imwrite("frame.png", frame)
        return "frame.png"

    def detect_text(self, path):
        self.last_read_text.clear()
        client = vision.ImageAnnotatorClient()
        with io.open(path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        print('Texts:')
        for text in texts:
            self.last_read_text.append(text.description)
            print('\n"{}"'.format(text.description))
            self.speak(text.description)

    def detect_objects(self, path):
        self.last_read_text.clear()
        client = vision.ImageAnnotatorClient()

        with open(path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        objects = client.object_localization(
            image=image).localized_object_annotations

        print('Number of objects found: {}'.format(len(objects)))
        memory_text = ""
        for object_ in objects:
            print('\n{} (confidence: {})'.format(object_.name, object_.score))
            self.last_read_text.append("There is a " + object_.name + "before you")
            memory_text = memory_text + "," + object_.name
            self.speak("There is a " + object_.name + "before you")
        self.memory.append(memory_text)

    def detect_emotion(self, path):
        self.last_read_text.clear()
        client = vision.ImageAnnotatorClient()
        with io.open(path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.face_detection(image=image)
        faces = response.face_annotations

        # Names of likelihood from google.cloud.vision.enums
        likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                           'LIKELY', 'VERY_LIKELY')
        print('Faces:')

        if len(faces) > 0:
            for face in faces:
                if likelihood_name[face.anger_likelihood] in self.possible_emotion:
                    text = "Person is " + likelihood_name[face.anger_likelihood] + " anger"
                    self.last_read_text.append(text)
                    self.speak(text)
                elif likelihood_name[face.joy_likelihood] in self.possible_emotion:
                    text = "Person is reacted " + likelihood_name[face.joy_likelihood] + "with joy"
                    self.last_read_text.append(text)
                    self.speak(text)
                elif (likelihood_name[face.surprise_likelihood] in self.possible_emotion):
                    text = "Person is " + likelihood_name[face.surprise_likelihood] + " suprised"
                    self.last_read_text.append(text)
                    self.speak(text)
                elif (likelihood_name[face.sorrow_likelihood] in self.possible_emotion):
                    text = "Person is " + likelihood_name[face.sorrow_likelihood] + " sorrow"
                    self.last_read_text.append(text)
                    self.speak(text)
                else:
                    text = "Person is reacted neutral"
                    self.last_read_text.append(text)
                    self.speak(text)
        else:
            self.last_read_text.append("no person infront of you or not straight to you")
            self.speak("no person infront of you or not straight to you")

    # detect_objects("bicycle.jpg")
    # detect_emotion("2022-11-20.png")
    # detect_emotion("frame.png")


while True:
    smart = SmartVisual()
    smart.get_command()