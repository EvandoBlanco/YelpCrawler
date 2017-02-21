import scrapy
import re
class YelpSpider(scrapy.Spider):
    #initial configuration
    name = "yelp"
    start_urls = ["https://www.yelp.com/biz/kramerbooks-and-afterwords-cafe-washington-3?sort_by=date_desc"]

    #parses for users on initial page
    def parse(self, response):
        #grabs users
        r = response.css("li.user-name a::attr(href)").extract()
        #check if users found
        if len(r) == 0:
            self.log("FAILED TO FIND USERS, MAKE SURE URL " + response.request.url + " IS A VALID PAGE")
        #Add users to requests
        else:
            for user in r:
                #request a user page, with reviews sorted by date & those in DC
                yield scrapy.Request("http://www.yelp.com"+user+"&review_filter=location&location_filter_city=Washington&location_filter_state=DC", self.userScrape)

            #insert new request, if no reveiws it will not create a request
            #get review start, add 20 to it and create a new request
            #if first response, need to add the start number
            if "start=" not in response.url:
                with open("testcsv.csv", "a") as o:
                    o.write("Name,Rating\n")
                t = response.url.split("?")
                n = t[0]+"?start=20&"+t[1]
                yield scrapy.Request(n, self.parse)
            #split out the start number and add
            else:
                t = re.split('[?]|[&]', response.url)
                i = int(t[1][t[1].find("=")+1:]) + 20
                t[1] = re.sub("[0-9]+", str(i), t[1])
                yield scrapy.Request(t[0]+"?"+t[1]+"&"+t[2],self.parse)


    #parses user pages for restaurants
    def userScrape(self, response):
        #grab reviews and ratings from customer page
        reviewedRests = response.css("a.biz-name.js-analytics-click span").extract()
        restRatings = response.css("div.biz-rating.biz-rating-large.clearfix div::attr(title)").extract()
        #make sure they're grabbed
        if len(reviewedRests) == 0 or len(restRatings) == 0 or len(restRatings) != len(reviewedRests):
            self.log("COULD NOT SCRAPE ANY BUSINESS NAMES OR RATINGS")
        #write to file
        else:
            with open("testcsv.csv", "a") as o:
                for i in range(len(restRatings)):
                    c = self.rep(reviewedRests[i],{",": " ", "<span>": "", "</span>": "", "&amp;": "&"})
                    s = c + "," + restRatings[i]
                    #change to ascii, or realistically change to a filetype that supports unicode
                    s = s.encode("ascii", "ignore")
                    o.write(s+"\n")
                    #get next page
                    # insert new request, if no reveiws it will not create a request
                    # get review start, add 20 to it and create a new request
                    # if first response, need to add the start number
                    if "start=" not in response.url:

                        yield scrapy.Request(response.url+"&rec_pagestart=10", self.userScrape)
                    # split out the start number and add
                    else:
                        i = response.url.rfind("=")
                        t = int(response.url[i+1:]) + 10
                        yield scrapy.Request(response.url[:i+1]+str(t), self.userScrape)

    #probably unnecessary
    #takes a dictionary of things to replace and what to replace them with
    def rep(self, s, toRep):
        for key in toRep:
            s = s.replace(key, toRep[key])
        return s