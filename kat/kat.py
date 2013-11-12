#!/usr/bin/env python

"""An unofficial Python API for http://kickass.to/
   Supports searching and getting popular torrents from the home page.
   Search results can be made more precise by using Categories and can
   be sorted according to file size, seeders etc.

   @author Stephan McLean
   @email stephan.mclean2@mail.dcu.ie

The MIT License (MIT)

Copyright (c) [2013] [Stephan McLean]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE."""

import bs4
import requests

def get_soup(page):
	"""Return BeautifulSoup object for given page"""
	request = requests.get(page)
	data = request.text
	return bs4.BeautifulSoup(data)

class Categories:
	ALL = "all"
	MOVIES = "movies"
	TV = "tv"
	ANIME = "anime"
	MUSIC = "music"
	BOOKS = "books"
	APPS = "applications"
	GAMES = "games"
	XXX = "xxx"

class Sorting:
	SIZE = "size"
	FILES = "files_count"
	AGE = "time_add"
	SEED = "seeders"
	LEECH = "leechers"

	class Order:
		ASC = "asc"
		DESC = "desc"

class Torrent(object):
	"""Represents a torrent as found in KAT search results"""

	def __init__(self, title, category, link, size, seed, leech, magnet,
				 download, files, age):
		self.title = title
		self.category = category
		self.page = "http://kickass.to" + link
		self.size = size
		self.seeders = seed
		self.leechers = leech
		self._magnet = magnet
		self._download = download
		self.files = files
		self.age = age
		self._data = None # bs4 html for getting download & magnet

	def print_details(self):
		"""Print torrent details"""
		print "Title:", self.title
		print "Category:", self.category
		print "Page: ", self.page
		print "Size: ", self.size
		print "Files: ", self.files
		print "Age: ", self.age
		print "Seeds:", self.seeders
		print "Leechers: ", self.leechers
		print "Magnet: ", self.magnet
		print "Download: ", self.download

	@property
	def download(self):
		if self._download:
			return self._download
		
		if self._data:
			self._download = self._data.find("a", class_="siteButton giantButton").get("href")
			return self._download

		# No data. Parse torrent page
		soup = get_soup(self.page)
		self._download = soup.find("a", class_="siteButton giantButton").get("href")
		self._data = soup # Store for later
		return self._download

	@property
	def magnet(self):
		if self._magnet:
			return self._magnet

		if self._data:
			self._magnet = self._data.find("a", class_="magnetlinkButton").get("href")
			return self._magnet

		soup = get_soup(self.page)
		self._magnet = soup.find("a", class_="magnetlinkButton").get("href")
		self._data = soup
		return self._magnet



class Search(object):
	"""This class will search for torrents given a search term or by
	   returning popular torrents from the home page. The results are
	   of type Torrent and can be iterated over."""

	base_url = "http://kickass.to/"
	search_url = "http://kickass.to/usearch/"
	latest_url = "http://kickass.to/new"

	def __init__(self):
		self.torrents = list()
		self._current_page = 1
		self.term = None
		self.category = None
		self.order = None
		self.sort = None
		self.current_url = None

	def search(self, term=None, category=None, pages=1, url=search_url,
				sort=None, order=None):
		"""Search a given URL for torrent results."""
	
		if not self.current_url:
			self.current_url = url

		print "Current url: ", self.current_url
		if self.current_url == Search.base_url:
			# Searching home page so no formatting
			results = self._get_results(self.current_url)
			self._add_results(results)
		else:

			search = self._format_search(term, category)
			sorting = self._format_sort(sort, order)

			# Now get the results.
			for i in range(pages):
				print "Getting: ", (search + "/" + str(self._current_page) + "/" + sorting)
				results = self._get_results(search + "/" + str(self._current_page) + 
											"/" + sorting)
				self._add_results(results)
				self._current_page += 1
			self._current_page -= 1

	def popular(self, category):
		self.search(url=Search.base_url)
		if category:
			self._categorize(category)

	def recent(self, category, pages, sort, order):
		self.search(pages=pages, url=Search.latest_url, sort=sort, order=order)
		if category:
			self._categorize(category)
		
	def _categorize(self, category):
		"""Remove torrents with unwanted category from self.torrents"""
		self.torrents = [result for result in self.torrents
						 if result.category == category]

	def _format_sort(self, sort, order):
		sorting = ""
		if sort:
			self.sort = sort
			sorting = "?field=" + self.sort
			if order:
				self.order = order
			else:
				self.order = Sorting.Order.DESC
			sorting = sorting + "&sorder=" + self.order
		return sorting

	def _format_search(self, term, category):
		search = self.current_url
		if term:
			self.term = term
			search = self.current_url + term

		if category:
			self.category = category
			search = search + " category:" + category
		return search

	def page(self, i):
		"""Get page i of search results"""
		# Need to clear previous results.
		self.torrents = list() 
		self._current_page = i 
		self.search(term=self.term, category=self.category, 
					sort=self.sort, order=self.order)

	def next_page(self):
		"""Get next page of search results."""
		self.page(self._current_page + 1)

	def _get_results(self, page):
		"""Find every div tag containing torrent details on given page, 
			then parse the results into a list of Torrents and return them"""
		
		soup = get_soup(page)
		details = soup.find_all("tr", class_="odd")
		even = soup.find_all("tr", class_="even")
		# Join the results 
		for i in range(len(even)):
			details.insert((i * 2)+1, even[i])

		return self._parse_details(details)

	def _parse_details(self, tag_list):
		"""Given a list of tags from either a search page or the
		   KAT home page parse the details and return a list of 
		   Torrents"""
   
		result = list()
		for i, item in enumerate(tag_list):
			title = item.find("a", class_="normalgrey font12px plain bold")
			title_text = title.text
			link = title.get("href")
			tds = item.find_all("td", class_="center") # Better name here.
			size = tds[0].text 
			files = tds[1].text
			age = tds[2].text
			seed = tds[3].text
			leech = tds[4].text
			magnet = item.find("a", class_="imagnet icon16")
			download = item.find("a", class_="idownload icon16")

			# Home page doesn't have magnet or download links
			if magnet:
				magnet = magnet.get("href")
			if download:
				download = download.get("href")

			# Get category changes depending on if we're parsing
			# the home page or a search page.
			if self.current_url == self.base_url:
				category = self._get_torrent_category(item, result=i)
			else:
				category = self._get_torrent_category(item)

			result.append(Torrent(title_text, category, link, size, seed,
								leech, magnet, download,files, age))

		return result

	def _get_torrent_category(self, tag, result=None):
		"""Given a tag containing torrent details try to find category
		   of torrent. In search pages the category is found in links of
		   the form <a href='/tv/'>TV</a> with TV replaced with movies, books
		   etc. For the home page I will use the result number to
		   decide the category"""
		
		hrefs = ["/movies/", "/tv/", "/music/", "/games/", "/applications/", "/anime/",
				 "/books/", "/xxx/"]
		category = None 
		if not result is None: # if result: 0 returns false. 
			# Searching home page, get category from result number
			category = hrefs[result / 10].strip("/")
			return category

		for item in hrefs:
			if tag.select("a[href=" + item + "]"):
				category = item.strip("/")
				return category


	def _add_results(self, results):
		for item in results:
			self.torrents.append(item)

	@property
	def current_page(self):
		return self._current_page

	def __iter__(self):
		return iter(self.torrents)

	def __len__(self):
		return len(self.torrents)

	def __getitem__(self, k):
		return self.torrents[k]


# Functions to be called by user -----------------------------------------
def search(term, category=Categories.ALL, pages=1, sort=None, order=None):
	"""Return a search result for term in category. Can also be 
		sorted and span multiple pages."""
	s = Search()
	s.search(term=term, category=category, pages=pages, sort=sort, order=order)
	return s

def popular(category=None):
	"""Return a search result containing torrents appearing
		on the KAT home page. Can be categorized. Cannot be
		sorted or contain multiple pages"""
	s = Search()
	s.popular(category)
	return s

def recent(category=None, pages=1, sort=None, order=None):
	"""Return most recently added torrents. Can be sorted and categorized 
		and contain multiple pages."""
	s = Search()
	s.recent(category, pages, sort, order)
	return s

# -----------------------------------------------------------------------
