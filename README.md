# Service Status Dashboard for Graphite

This project is targeted for those who uses [graphite](http://graphite.wikidot.com) for gathering statistics from several servers/routers/whatever andwants to see it as graphs or summary tables on a dashboard which is hopefully slightly better than the Graphite's dashboard.

You can define graphs or tables to see on the dashboard using very simple yaml based config file. Here's a short sample. Imagine you have several groups of similar set up servers. Let's name these groups as 'proxies', 'backends' and 'databases'. For every group we can define what to show on 'summary' page and on every server's individual pages. So let's assume we want to see a load average graph of top 3 most loaded backend servers on backends' summary page and load average and eth0 bandwidth usage on individual server's pages as graphs and total hits of top 3 most visited sites grouped by day as tables. Then our config file `./conf/config.yaml` would look like this:

    backends:
      nodes:
        - summary:
          graphs:
            - '/render/?target=aliasByNode(highestMax(backends.*.loadavg,3),1)&title=Top 3 highest loadavg'
        - be1
        - be2
        - be3
         ...
        - be10
      graphs:
        - '/render/?target=backends.$name.loadavg'
        - '/render/?target=alias(scale(scaleToSeconds(nonNegativeDerivative(backends.$name.eth0.tx_bytes),1),8),"bytes in")&target=alias(scale(scaleToSeconds(nonNegativeDerivative(backends.$name.eth0.rx_bytes),1),8),"bytes out")&title=$name eth0'
      tables:
        - 
          title: '$name most visited sites'
          url: '/render/?target=aliasByNode(highestMax(summarize(backends.$name.sites.*.hits,"1day","sum"),3),4)&format=json'
    proxies:
      ...
    databases:
      ...

Probably you have noticed we used an alias `$name` here. It is always replaced with server's name which page is to be shown. You an also define individual graphs or tables for every server defining it's individual `graphs:` and `tables:` sections using the same format as above.
