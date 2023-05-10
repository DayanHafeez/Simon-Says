from PIL import Image, ImageTk
import tkinter as tk
import cv2
from PoseComparison import isPoseCorrect
import serial 


class App:
    reset_time = 5
    reset_delay = reset_time

    reset_time += 2  #2 seconds overhead for the timer to compensate for the time taken to load video feed
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simon Says")
        self.root.geometry("1920x1080")
        self.image_list = [
            r"resources\refImage.webp",
            r"resources\refImage.webp",
            r"resources\refImage.webp"
        ]
        self.logo_address = r"resources\logo.png"
        self.remaining_time = App.reset_time 
        self.timer_label = tk.Label(self.root, text=f"Time remaining: {self.remaining_time}", font=("Arial", 24))
        self.timer_label.place(relx=0.1, rely=0.1, anchor="center")
        self.timer_id = None
        self.timer_label.place_forget()
        self.current_image = 0
        
        # Open the image using PIL
        logo = Image.open(self.logo_address)

        # Resize the image
        logo = logo.resize((100, 100), Image.LANCZOS)

        # Create an object of tkinter ImageTk
        self.logo_img = ImageTk.PhotoImage(logo)

        # Create a Label Widget to display the text or Image
        self.logo_label = tk.Label(self.root, image=self.logo_img)
        self.logo_label.pack()

        self.game_title = tk.Label(self.root, text="Simon Says", font=("Arial", 48))
        self.game_title.place(relx=0.5, rely=0.2, anchor="center")
        self.exitbutton = tk.Button(self.root, text="Exit", command=self.exit_app)
        self.exitbutton.place(relx=0.9, rely=0.9, anchor="center")
        self.startbutton = tk.Button(self.root, text="Start", command=self.start)
        self.startbutton.place(relx=0.5, rely=0.5, anchor="center")

    def start(self):
        self.game_title.destroy()
        self.logo_label.destroy()
        self.change_background()

    def change_background(self):
        try:
            self.startbutton.destroy()
        except:
            pass
        self.show_ready()

    def exit_app(self):
        self.root.destroy()

    def show_ready(self):
        self.ready_label = tk.Label(self.root, text="Ready!", font=("Arial", 48))
        self.ready_label.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(1000, self.destroy_ready)

    def destroy_ready(self):
        self.ready_label.destroy()
        self.show_go()

    def show_go(self):
        self.go_label = tk.Label(self.root, text="GO!", font=("Arial", 48))
        self.go_label.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(1000, self.destroy_go)

    def destroy_go(self):
        self.go_label.destroy()
        self.show_image()
    
    def reset_timer(self):
        self.remaining_time = App.reset_time
        self.timer_label.config(text=f"Time remaining: {self.remaining_time}")
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.update_timer()


    def pause_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def resume_timer(self):
        if self.timer_id is None:
            self.update_timer()

    def winflag(self, liveImg):
        self.pause_timer()
        try:
            result = isPoseCorrect(self.image_list[self.current_image], liveImg, threshold=10)
        except TypeError:
            self.exit_app()
            raise "The reference image does not contain a person"
        except UnboundLocalError:
            self.exit_app()
            raise "person is not in the frame"
        self.resume_timer()
        return result


    def show_image(self):
        if self.current_image == len(self.image_list):
            # Display "Game Ended" message and "Play Again" button
            self.background_label.destroy()
            self.timer_label.place_forget()
            self.play_again_button = tk.Button(self.root, text="Play Again", command=self.play_again)
            self.play_again_button.place(relx=0.5, rely=0.6, anchor="center")
        else:
            # Display the next image
            image_path = self.image_list[self.current_image]
            try:
                image = Image.open(image_path)
            except  FileNotFoundError:
                self.exit_app()
                raise "The reference image does not exist (file not found)"
            image = image.resize((800, 600), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.background_label = tk.Label(self.root, image=photo)
            self.background_label.image = photo
            self.background_label.place(relx=0.5, rely=0.5, anchor="center")
            if self.current_image == 0:
                self.timer_label.place(relx=0.1, rely=0.1, anchor="center")

            # Reset and start the timer
            self.reset_timer()
            # Start displaying the video feed 
            liveImg = self.display_video_feed()

            # Check if the player has won
            if self.winflag(liveImg):
                # Increment current_image and schedule the next call to show_image
                self.current_image += 1
                self.level_up()
                self.timer_label = tk.Label(self.root, text=f"Time remaining: {self.remaining_time}", font=("Arial", 24))
                self.timer_label.place(relx=0.1, rely=0.1, anchor="center")
                self.root.after(App.reset_delay, self.show_image)
            else:
                # Exit the app if the player loses
                self.endloss()
                
    def endloss(self):
        self.timer_label.place_forget()
        self.endcard = tk.Label(self.root, text="You LOSE!\nYou have brought shame to your family.\nDo you want to regain your honor?", font=("Arial", 48))
        self.endcard.place(relx=0.5, rely=0.5, anchor="center")
        self.okbutton = tk.Button(self.root, text="Yes", command=self.finalcard)
        self.okbutton.place(relx=0.5, rely=0.7, anchor="center")

    def finalcard(self):
        self.endcard.destroy()
        self.okbutton.destroy()
        self.fcard = tk.Label(self.root, text="There are no retries in life!!!", font=("Arial", 48))
        self.fcard.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(App.reset_delay, self.run_arduino)
        self.root.after(5000, self.exit_app)

    def run_arduino(self):
        # print("arduino ran")
        try:
            ser = serial.Serial('COM5', 9600)
        except:
            raise "Arduino not connected"
        ser.write(b'1011')        
        ser.close()

    def level_up(self):
        self.pause_timer()
        self.background_label.destroy()
        self.timer_label.place_forget()
        if (self.current_image == len(self.image_list)):
            self.game_ended_label = tk.Label(self.root, text="  Congratulations! You WIN!  ", font=("Arial", 48))
            self.game_ended_label.place(relx=0.5, rely=0.4, anchor="center")
            self.play_again_button = tk.Button(self.root, text="Play Again", command=self.play_again)
            self.play_again_button.place(relx=0.5, rely=0.6, anchor="center")
            return
        self.level_up_label = tk.Label(self.root, text="   You survived the round!!   ", font=("Arial", 48))
        self.level_up_label.place(relx=0.5, rely=0.4, anchor="center")

    def destroy_level_up(self):
        self.level_up_label.destroy()
        self.resume_timer()
        

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_label.config(text=f"Time remaining: {self.remaining_time}")
            self.timer_id = self.root.after(1000, self.update_timer)
        else:
            # Close the video feed here
            self.close_video_feed()
    
    def display_video_feed(self):
        # Create a Label widget to display the video feed
        self.video_label = tk.Label(self.root)
        self.video_label.place(relx=1.0, rely=0.0, anchor="ne")

        # Start video capture using cv2
        cap = cv2.VideoCapture(0)
        # fps = cap.get(cv2.CAP_PROP_FPS)
        # print(fps)

        # Continuously read and display frames from the video capture
        while self.remaining_time > 0:
            ret, frame = cap.read()

            # Convert the frame from BGR to RGB color space
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            
            # Convert the frame to a PIL Image
            image = Image.fromarray(image)
        
            # Convert the PIL Image to a PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Update the Label widget with the PhotoImage
            self.video_label.config(image=photo)
            self.video_label.image = photo

            #  Update the GUI and wait for 10 milliseconds
            self.root.update()
            self.root.after(10)

        # Release the video capture and destroy all cv2 windows
        cap.release()
        cv2.destroyAllWindows()
        return frame
    
    def close_video_feed(self):
        # Stop the video capture by setting the remaining_time to 0
        self.remaining_time = 0

        # Destroy the Label widget displaying the video feed
        self.video_label.destroy()

    def play_again(self):
        # Reset current_image and start the game again
        self.current_image = 0
        self.level_up_label.destroy()
        self.game_ended_label.destroy()
        self.play_again_button.destroy()
        self.show_image()


app = App()
app.root.mainloop()


