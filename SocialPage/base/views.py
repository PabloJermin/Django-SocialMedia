from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout   
from django.contrib.auth.forms import UserCreationForm 
from .models import Room, Topic, Message
from .forms import RoomForm 

# rooms = [
#     {'id': 1, 'name': 'quality Control'},
#     {'id': 2, 'name': 'quality Assurance'},
#     {'id': 3, 'name': 'Computer Science'},
# ]
def loginPage(request):
    page = "login"
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, "User does not exist") 

        user = authenticate(request, username = username, password = password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username OR password does not exist")
        
    context = {"page" : page}
    return render (request, "base/loginpage.html", context)



def logoutUser(request):
    logout(request)
    return redirect('home')


def registerUser(request):    
    form = UserCreationForm()
    
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid:
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect( 'home')
        else:
            messages.error(request, "An error occured during registration") 
    
    return render (request, "base/loginpage.html", {
        "form " : form
    } )


def home(request):
    q = request.GET.get('q') if request.GET.get('q')!= None else ""
    
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains= q)) 
    topics = Topic.objects.all()
    room_count = rooms.count() 
    room_messages = Message.objects.all().filter(Q(room__topic__name__icontains= q))
    
    if room_count == 0:
        room_count = "No "
    
    return render(request, 'base/home.html', {'rooms': rooms, 'topics': topics, 'room_count': room_count,
                                              "room_messages": room_messages})



def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    
    if request.method == "POST":
        message = Message.objects.create(
            user  = request.user,
            room  = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    return render(request, 'base/room.html', {
        'room': room,
        "room_messages": room_messages,
        'participants': participants,
    })
    

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    room = user.room_set.all()
    # select all the messages posted by the user
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context= {'user': user,
              'room': room,
              'room_messages': room_messages,
              'topics': topics}
    
    return render(request, 'base/profile.html', context)
    
    
@login_required(login_url = "login")   
def create_room(request):
    form = RoomForm()
    if request.method == "POST":
        form = RoomForm(request.POST)
        # creating a host according to the user logged in
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
    context= {
        'form' : form        
    }
    return render(request, 'base/room_form.html', context)



@login_required(login_url = "login")  
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance = room)
    
    if request.user != room.host:
        return HttpResponse("You are not allowed here")
    # prefill the content of the room form with already existing info
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
        return redirect('home')       
    
    context= {
        'form': form
    }
    return render(request, 'base/room_form.html', context)



@login_required(login_url = "login")  
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})



@login_required(login_url = "login")  
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    if message.user != request.user:
        return HttpResponse("You can't delete this")
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})