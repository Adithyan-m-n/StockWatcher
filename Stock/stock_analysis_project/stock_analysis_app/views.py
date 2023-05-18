from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SearchHistory, User
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
import yfinance as yf
import matplotlib.pyplot as plt
import io
import urllib, base64
import requests
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date



def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('analysis')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def analyze_stock_view(request):
    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol', '')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')

        # Parse the start and end dates
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        # Fetch the stock data from Yahoo Finance
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        # Get additional stock information
        stock_info = yf.Ticker(stock_symbol).info


        # Fetch short company description using API
        company_description = stock_info.get('longBusinessSummary', '')
        # Extract the desired columns
        stock_prices = stock_data[['Open', 'Low', 'High', 'Close', 'Volume']]

        # Save each plot as a separate image file
        image_files = []
        for column in stock_prices.columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(stock_prices.index, stock_prices[column])
            ax.set_title(column)
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')

            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            image_files.append(image_base64)
            buffer.close()

            plt.close(fig)

        # Save the search history for the user
        user = request.user
        search_history = SearchHistory(stock_symbol=stock_symbol, start_date=start_date, end_date=end_date, user=user)
        search_history.save()
        history = SearchHistory.objects.filter(user_id=user.id).order_by('-created_at')

        return render(request, 'analyze_stock.html', {'image_files': image_files, 'search_history': history, 'stock_info': stock_info, 'company_description': company_description})
    else:
        user = request.user
        history = SearchHistory.objects.filter(user_id=user.id).order_by('-created_at')
        if 'clear_history' in request.GET:
                # Clear search history
                history.delete()
                messages.success(request, 'Search history cleared successfully.')

                return redirect('analysis')

        return render(request, 'analyze_stock.html', {'search_history': history})



