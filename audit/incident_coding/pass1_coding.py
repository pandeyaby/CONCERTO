import csv,re,unicodedata,json
AD='2026-10-15'
def norm(s):
    s=s.replace('\u2019',"'").replace('\u2018',"'").replace('\u201c','"').replace('\u201d','"').replace('\u2026','...')
    return re.sub(r'\s+',' ',s).strip()
# id, org, date, title, url, txtfile, source_type, mechanisms, channels(pass1, primary first), conf, decision, excl, quote1, quote2, notes
R=[]
def inc(**k): R.append(k)
inc(id='I01',org='AWS',date='2011-04-21',title='Amazon EC2 and Amazon RDS service disruption, US East (EBS re-mirroring storm)',url='https://aws.amazon.com/message/65648/',txt='aws65648',src='vendor PES',
 mech='automatic EBS re-mirroring (re-replication); re-mirroring search with insufficient back-off; control-plane API timeout policy',ch='T',conf='medium',dec='include',ex='',
 q1='Because the EBS control plane (and the create volume API in particular) was configured with a long time-out period, these slow API calls began to back up and resulted in thread starvation in the EBS control plane.',
 q2='the nodes failing to find new nodes did not back off aggressively enough when they could not find space, but instead, continued to search repeatedly.',
 notes='Trigger: incorrect manual traffic shift. Re-mirroring storm (redistributive recovery action) exhausted capacity; long timeouts turned it into regional thread starvation.')
inc(id='I02',org='AWS',date='2014-06-13',title='Amazon SimpleDB service disruption, US East',url='https://aws.amazon.com/message/65649/',txt='aws65649',src='vendor PES',
 mech='lock-service failure detection / de-registration; handshake timeout + retry; node self-removal from cluster',ch='T',conf='high',dec='include',ex='',
 q1='the server failure pattern in this event resulted in a sudden and significant increase in load on the lock service as it rapidly de-registered the failed storage nodes from their respective replication groups.',
 q2='After several handshake retries and subsequent timeouts, SimpleDB storage and metadata nodes removed themselves from the SimpleDB production cluster',
 notes='Trigger: power loss to storage nodes. AWS: self-removal after timeouts "increased the scope of the event".')
inc(id='I03',org='AWS',date='2015-09-20',title='Amazon DynamoDB service disruption, US East',url='https://aws.amazon.com/message/5467D2/',txt='aws5467D2',src='vendor PES',
 mech='membership-request timeout + retry; storage-server self-disqualification from serving',ch='T',conf='medium',dec='include',ex='',
 q1="If the storage servers aren't able to retrieve this membership data back within a specific time period, they will retry the membership request and temporarily disqualify themselves from accepting requests.",
 q2='Unavailable servers continued to retry requests for membership data, maintaining high load on the metadata service.',
 notes='Borderline on independence: retry and self-disqualification are parts of the same membership-renewal logic (see pass 2).')
inc(id='I04',org='Google / Niantic',date='2016 (summer; exact date not given)',title='Pokemon GO on GCLB (SRE Workbook ch. 11, Case Study 1)',url='https://sre.google/workbook/managing-load/',txt='sreload',src='first-party book case study',
 mech='load-balancer (GFE) retry of GET requests; client app retry (single immediate retry then constant backoff)',ch='T',conf='high',dec='include',ex='',
 q1='Under this circumstance, the load balancer retried GET requests, adding to the system load.',
 q2='These error responses served to effectively synchronize client retries, producing a "thundering herd" problem',
 notes='Two retry layers owned by different parties (Google LB, Niantic client). Remedy included LB admission override and client jitter.')
inc(id='I05',org='Discord',date='2017-03-20',title='Connectivity Issues (presence/sessions)',url='https://status.discordapp.com/incidents/dj3l6lw926kl',txt='discord1',src='vendor status postmortem',
 mech='session-service reconnect to presence (retry); session buffer-and-retransmit queueing',ch='T',conf='low',dec='include',ex='',
 q1='The failure of the individual presence node caused all the Erlang processes living in our session service to attempt a reconnection to the aforementioned presence service.',
 q2='The events and messages for these connections quickly filled the in-memory buffers of our session servers and caused many of them to run out of memory and fail.',
 notes='Buffering is a reliability mechanism but outside the codebook class list; borderline (see pass 2). Trigger: CPU soft lockups + split-brain bug.')
inc(id='I06',org='Slack',date='2021-01-04',title="Slack's Outage on January 4th 2021",url='https://slack.engineering/slacks-outage-on-january-4th-2021/',txt='slack2021',src='vendor engineering blog',
 mech='health-check-driven instance replacement; autoscaler (CPU + Apache worker-thread utilization); LB panic mode; retries and circuit breaking',ch='A;T',conf='high',dec='include',ex='',
 q1="Some of our instances were marked unhealthy by our automation because they couldn't reach the backends that they depended on. Our systems attempted to replace these unhealthy instances with new instances. Secondly, our autoscaling system downscaled our web tier.",
 q2='We will also reevaluate our health-checking and autoscaling configurations to prevent inadvertently overloading provision-service again',
 notes='Two capacity actuators (replacement, autoscaling) acted concurrently on instance provisioning; combined 1,200-instance scale-up overloaded provision-service. CPU signal fell because threads waited on the network (signal distortion not caused by a peer mechanism).')
inc(id='I07',org='Auth0',date='2021-04-20',title='US-1 Full Service Disruption - Detailed Root Cause Analysis',url='https://cdn.auth0.com/blog/Detailed_Root_Cause_Analysis_(RCA)_4-2021.pdf',txt='auth0rca',src='vendor RCA (PDF)',
 mech='cache-bypass fallback; client timeout + retry; utilization-based autoscaler',ch='O;T',conf='high',dec='include',ex='',
 q1='As front-end API nodes stopped receiving timely responses, they retried performing the original queries, and more incoming requests were added to the queue.',
 q2='The increased number of in-flight requests due to long query times caused increased utilization, causing them to quickly scale to the maximum number of instances.',
 notes='Retry/in-flight work inflated the autoscaler signal (observation); scale-out 37->100 added DB load (topological). Recovery required manual scale-down to 45. Not from the user-listed vendor set; found via search, primary PDF verified.')
inc(id='I08',org='AWS',date='2021-12-07',title='AWS service event, US-EAST-1 (internal network congestion)',url='https://aws.amazon.com/message/12721/',txt='aws12721',src='vendor PES',
 mech='automated capacity scaling; client connection retry / back-off',ch='T',conf='high',dec='include',ex='',
 q1='an automated activity to scale capacity of one of the AWS services hosted in the main AWS network triggered an unexpected behavior from a large number of clients inside the internal network.',
 q2='These delays increased latency and errors for services communicating between these networks, resulting in even more connection attempts and retries.',
 notes='AWS: a latent issue prevented clients from backing off; scaling activity disabled as remediation.')
inc(id='I09',org='AWS',date='2025-10-20',title='Amazon DynamoDB service disruption, US-EAST-1 (NLB phase)',url='https://aws.amazon.com/message/101925/',txt='aws101925',src='vendor PES',
 mech='NLB health checks; automatic AZ DNS failover; health-check-triggered instance termination',ch='T',conf='high',dec='include',ex='',
 q1='The alternating health check results increased the load on the health check subsystem, causing it to degrade, resulting in delays in health checks and triggering automatic AZ DNS failover to occur.',
 q2='For multi-AZ load balancers, this resulted in capacity being taken out of service.',
 notes='Only the NLB phase qualifies; the DynamoDB DNS race (root trigger) is a single automation defect. AWS remedy: velocity control limiting capacity removed by failover.')
inc(id='I10',org='Discord',date='2026-03-25',title='Behind the Scenes of the 3/25/26 Voice Outage',url='https://discord.com/blog/behind-the-scenes-of-the-3-25-26-voice-outage',txt='discord2026',src='vendor engineering blog',
 mech='gateway-driven client reconnect; per-host session-start rate limit; health-based hash-ring placement with secondary/tertiary failover; RPC retries',ch='T',conf='medium',dec='include',ex='',
 q1='Because the majority of our instances were not in the ring, healthy instances were accepting additional traffic acting as the secondary and tertiary failover for unhealthy instances.',
 q2="As these requests arrived, they triggered our start session rate limit that provides backpressure when we have a flood of requests... but that rate limit hadn't yet been re-tuned after the migration.",
 notes='Trigger: operator-initiated pod resize. Not in the user-listed vendor archives search; found via web search.')
inc(id='I11',org='GitHub',date='2026-08-17',title='GitHub availability report: August 2026 (Aug 17 incident)',url='https://github.blog/news-insights/company-news/github-availability-report-august-2026/',txt='gh2026aug',src='vendor availability report',
 mech='service-mesh sidecar concurrency limit; autoscaler (scaled on host service); gateway retries; client retries',ch='T;O',conf='medium',dec='include',ex='',
 q1='The core weakness was that our service-mesh sidecar did not scale up, together with our retry behavior, and clients were not bound enough to keep a partial degradation from amplifying into a broader overload.',
 q2='Correct autoscaling policies so they account for service-mesh sidecar concurrency and capacity, not just the host service.',
 notes='Observation coding is inferred from the remediation (autoscaler blind to the limiter), not stated as masking.')
# exclusions
def exc(id,org,date,title,url,txt,code,reason,src='vendor PES'):
    R.append(dict(id=id,org=org,date=date,title=title,url=url,txt=txt,src=src,mech='',ch='',conf='',dec='exclude',ex=code,q1='',q2='',notes=reason))
exc('X01','AWS','2011-08-07','EC2/EBS/RDS event, EU West (power)','https://aws.amazon.com/message/2329B7/','aws2329B7','E3','Power loss; RDS failover health check impaired by DNS. One mechanism (failover) in causal chain.')
exc('X02','AWS','2012-06-29','AWS service event, US East (power)','https://aws.amazon.com/message/67457/','aws67457','E4','Power loss; ELB traffic-shift backlog and RDS failover bug. No mechanism-mechanism interaction described as causal.')
exc('X03','AWS','2012-10-22','EC2/EBS/RDS/ELB event, US East','https://aws.amazon.com/message/680342/','aws680342','E3','Memory-leak bug in reporting agent; EBS failover lacked healthy targets; aggressive API throttling was an operator-applied policy. Only one automated mechanism in causal chain.')
exc('X04','AWS','2012-12-24','Amazon ELB event, US East','https://aws.amazon.com/message/680587/','aws680587','E3','Operator process deleted ELB state data; no mechanism interaction.')
exc('X05','AWS','2013-12-17','South America (SA-EAST-1) power event','https://aws.amazon.com/message/656481/','aws656481','E3','Datacenter power/generator controls; outside service-level mechanism scope.')
exc('X06','AWS','2016-06-04','AWS service event, Sydney (power)','https://aws.amazon.com/message/4372T8/','aws4372T8','E3','Power loss; manual failover of control plane. No interacting mechanisms.')
exc('X07','AWS','2017-02-28','Amazon S3 disruption, US-EAST-1','https://aws.amazon.com/message/41926/','aws41926','E3','Operator command typo removed servers; no mechanism interaction.')
exc('X08','AWS','2018-11 (summary dated 2018-11-22)','EC2 DNS resolution issues, Seoul','https://aws.amazon.com/message/74876-2/','aws74876','E3','Config change removed minimum-healthy-hosts setting; single health-based mechanism.')
exc('X09','AWS','2019-08-23','EC2 issues, Tokyo (cooling control)','https://aws.amazon.com/message/56489/','aws56489','E3','Datacenter cooling control-system failover bug; outside service-level mechanism scope.')
exc('X10','AWS','2020-11-25','Amazon Kinesis event, US-EAST-1','https://aws.amazon.com/message/11201/','aws11201','E3','Operator capacity addition exceeded OS thread limit; health-based removal mentioned only as a recovery constraint.')
exc('X11','AWS','2021-09-02','Direct Connect event, Tokyo','https://aws.amazon.com/message/17908/','aws17908','E3','Network OS defect in a new failover protocol; single mechanism/defect.')
exc('X12','AWS','2023-06-13','AWS Lambda event, US-EAST-1','https://aws.amazon.com/message/061323/','aws061323','E3','Lambda frontend capacity-management defect; throttles applied manually as mitigation.')
exc('X13','AWS','2024-07-30','Amazon Kinesis Data Streams event, US-EAST-1','https://aws.amazon.com/message/073024/','aws073024','E5','Work balancing and health determination are both functions of one cell-management system; fails independence criterion despite an observation-like path (large status messages -> false unhealthy -> redistribution).')
exc('X14','Slack','2022-02-22',"Slack's incident on 2-22-22",'https://slack.engineering/slacks-incident-on-2-22-22/','slack2022','E3','Cache-node replacement + client retries; client-boot throttle was applied manually. One automated mechanism (client retries) in the causal chain.',src='vendor engineering blog')
exc('X15','GitHub','2018-10-21','October 21 post-incident analysis','https://github.blog/news-insights/company-news/oct21-post-incident-analysis/','github2018','E3','Network partition triggered Orchestrator MySQL failover; single mechanism.',src='vendor engineering blog')
exc('X16','GitHub','2022-03 (Mar 16-23)','An update on recent service disruptions','https://github.blog/2022-03-23-an-update-on-recent-service-disruptions/','gh2022','E3','ProxySQL connection exhaustion; failovers and webhook throttling were operator actions.',src='vendor engineering blog')
exc('X17','Meta','2021-10-04','More details about the October 4 outage','https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/','fb2021','E3','Backbone withdrawn by a command + audit-tool bug; DNS servers withdrew BGP on failed health checks (single mechanism).',src='vendor engineering blog')
exc('X18','Google Cloud','2025-06-12','Service Control outage (multiple products)','https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW','gcp2025','E3','Null-pointer crash loop; missing randomized backoff caused herd on Spanner. Single mechanism (restart/retry); throttling manual.',src='vendor status report')
exc('X19','Google Cloud','2020-12-14','Google OAuth / User ID Service outage','https://status.cloud.google.com/incident/zall/20013','gcp2020','E3','Automated quota system reduced quota from a usage value mis-reported by a leftover migration component; one actuating mechanism.',src='vendor status report')
exc('X20','Google Cloud','2022-09-13','Filestore global API throttling','https://status.cloud.google.com/incidents/X8SNkK2BPyCrc1sveeiu','filestore','E3','Malfunctioning internal client tripped a global API limit; single mechanism.',src='vendor status report')
exc('X21','Google Cloud','2019-03-12','Cloud Storage / blob lookup overload (19002)','https://status.cloud.google.com/incident/storage/19002','gcs19002','E3','SRE configuration change overloaded metadata lookup; load shedding mentioned only as remediation.',src='vendor status report')
exc('X22','Cloudflare','2019-07-02','Details of the Cloudflare outage on July 2, 2019','https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/','cf2019','E3','WAF regex CPU exhaustion; no mechanism interaction.',src='vendor engineering blog')
exc('X23','Cloudflare','2024-06-20','Cloudflare incident on June 20, 2024','https://blog.cloudflare.com/cloudflare-incident-on-june-20-2024/','cf2024','E4','New DDoS rule exposed a latent bug in the rate limiter (interaction via code defect); separate automated reroute caused backbone congestion (single mechanism).',src='vendor engineering blog')
exc('X24','Cloudflare','2025-11-18','Cloudflare outage on November 18, 2025','https://blog.cloudflare.com/18-november-2025-outage/','cf2025','E3','Oversized bot-management feature file; retries only during dashboard recovery.',src='vendor engineering blog')
exc('X25','Roblox','2021-10-28','Return to service 10/28-10/31 2021','https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021','roblox','E3','Consul streaming/BoltDB contention; health-check load is a single mechanism.',src='vendor newsroom')
exc('X26','Fastly','2021-06-08','Summary of June 8 outage','https://www.fastly.com/blog/summary-of-june-8-outage','fastly','E3','Latent software bug triggered by customer config; no mechanism interaction.',src='vendor blog')
exc('X27','Stripe','2019-07-10','Root cause analysis: elevated error rates on 2019-07-10','https://stripe.com/rcas/2019-07-10','stripe2','E3','Database election defect with stalled-but-healthy nodes; single failover mechanism.',src='vendor RCA')
exc('X28','Microsoft Azure','2024-07-30','Azure Front Door/CDN PIR (KTY1-HW8)','https://azure.status.microsoft/en-us/status/history/?trackingId=KTY1-HW8','azure2024','E3','DDoS protection could not disengage at one site (control-plane power failure) + latent routing config; single protective mechanism.',src='vendor PIR')
exc('X29','Discord','2017-10-13','Unavailable Guilds & Connection Issues','https://status.discordapp.com/incidents/qk9cdgnqnhcn','discord2','E4','Automatic Redis HA failover exposed client failover-handling defect; interaction via code defect.',src='vendor status postmortem')
exc('X30','LaunchDarkly','2025-10-20','Our October 20 Service Disruption','https://launchdarkly.com/blog/what-happened-what-we-learned-and-how-were-improving/','launchdarkly','E3','Operator load-reduction change reverted routing to cold caches, causing SDK retries; autoscaling blocked by AWS dependency, not by a peer mechanism.',src='vendor blog')
exc('X31','Spotify','2013 (approx.; blog dated 2013-06-04)','Incident Management at Spotify','https://labs.spotify.com/2013/06/04/incident-management-at-spotify/','spotify','E3','Client retries without backoff overloaded Popcount; single mechanism.',src='vendor engineering blog')
exc('X32','Google (SRE Workbook)','n/a','Case Study 2: When Load Shedding Attacks ("Dressy")','https://sre.google/workbook/managing-load/','sreload','E2','Explicitly a fictional company; mechanism (shedding hides errors from utilization-aware LB) is relevant practitioner literature, cited separately, not an incident.',src='first-party book')
exc('X33','Heroku','unknown','Heroku status incident 2451','https://status.heroku.com/incidents/2451','heroku','E1','Page renders client-side only; content could not be retrieved or verified.',src='vendor status page')
exc('X34','Chef','2014-07','Supermarket intermittent unresponsiveness postmortem','https://www.chef.io/blog/2014/07/10/supermarket-intermittent-unresponsiveness-postmortem/','chef','E1','Public post is a summary; full postmortem in a private repository. Insufficient detail.',src='vendor blog')
json.dump(R,open('./pass1.json','w'),indent=1)
# verify quotes
bad=0
for r in R:
    t=norm(open('./'+r['txt']+'.txt',errors='ignore').read())
    for q in (r['q1'],r['q2']):
        if q and norm(q) not in t:
            print('QUOTE NOT FOUND',r['id'],q[:80]); bad+=1
print('records',len(R),'bad quotes',bad, 'included',sum(r['dec']=='include' for r in R))
