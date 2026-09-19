"""Preload the master catalog of approved enrichment items (name + category).

Transcribed from "Enrichment Calendars v4 - Master List Template.pdf". Items
with no category in the source get the "Unknown" category, per instruction.
These items have no photo yet -- that gets uploaded later, per item, via
/admin (Enrichment.save() and the templates were made to tolerate a missing
photo for exactly this reason).

Each line below is "Item Name|Category" (empty category -> Unknown).
Run with: python3 manage.py import_enrichment_master_list
"""
from django.core.management.base import BaseCommand

from ents.models import Enrichment
from zoo.models import ItemCategory

ITEMS_TEXT = """
Air tubing sticks: over 12" in length -  nesting material|General
Alfalfa|Food
Animal Feces|Biological
Animal Hide- Deer/ Rabbit < 5" X 5"|Biological
Animal Hide- Deer/ Rabbit > 5" X 5"|Biological
Antler|General
Antler-2.5” wide|General
Antlers- All|Range
Antlers-spikes|General
Apple Chew Sticks|Chew Toy
Apple sauce|Food
Approved Browse|Food
Approved Fresh Herbs/ Spices/ Flowers|Food
Aquarium decor-hard plastic|General
Aquarium plants-plastic|General
Astro PVC Tube|General
Astroturf 5"X5" or larger pieces- No loose strings|Range
Astroturf square - hanging|General
Avocado - no pit or skin|Food
Baby Bottle|General
Baby food ( meat)|Food
Baby food (fruit and vegetable)|Food
Baby tambourine|General
Baking sheets - Metal- various sizes|General
Ball - 18”- Tiger Hard Plastic – Grey|Ball
Ball - 4” with holes-hanging-hard plastic|Ball
Ball - 6” with holes-hanging- hard plastic|Ball
Ball - 8” hanging -hard plastic|Ball
Ball - Jingle- 17” dia. with 1.5” holes- Tiger Hard Plastic|Ball
Ball - plush-tiny|Ball
Ball - small- rubber|Ball
Ball - small-wooden|Ball
Ball -12”- Exercise|Ball
Ball -5.5”- Exercise|Ball
Ball -9”-Tug n Toss|Ball
Ball -Jingle - 6”- hard plastic|Ball
Ball and tube toy - soft plastic and PVC|Ball
Ball Bumbal|Ball
Ball pit balls - 2.5” soft plastic|Ball
Ball Red on Chain- Hanging- Hard Plastic|Ball
Ball- 8” with 1.75” holes-thick rubber|Ball
Ball- 10”- Hard Plastic|Ball
Ball- 12” with 2” hole-Hard Plastic|Ball
Ball- 12”-Tiger Hard Plastic|Ball
Ball- 13”- Hard Plastic|Ball
Ball- 20”- Hard Plastic|Ball
Ball- 4"-20"- holes less than 2" hard plastic/ Tiger hard plastic|Range
Ball- 4"-20"- no hole- hard plastic/ Tiger hard plastic|Range
Ball- 4"-8" - holes less than 2" hard plastic/ Tiger hard plastic|Range
Ball- 4"-8" - no hole hard plastic/ Tiger hard plastic|Range
Ball- 5” with 1” hole-soft rubber|Ball
Ball- 5”-Tennis|Ball
Ball- 6”- Hard Plastic|Ball
Ball- 9” Hard Plastic|Ball
Ball- Ball Pit Ball Small|Ball
Ball- Bunjee - Aussie Dog|Ball
Ball- Fillable- thin plastic|Ball
Ball- Foobler Mechanical Treat Dispenser|Ball
Ball- Jolly-9“ with 1” Hole- Hard Plastic|Ball
Ball- Rubber- Inflated- XL|Ball
Ball- Sensory Metal - 13 1/4”|Ball
Ball- Sensory Metal - Size 2.36”|Ball
Ball- Sensory Metal - Size 3.15”|Ball
Ball- Sensory Metal - Size 3.49”|Ball
Ball- Sensory Metal - Size 5.9”|Ball
Ball- Teaser- 10”|Ball
Ball- Teaser- 8”|Ball
Ball- Tennis- standard|Ball
Ball- Wiffle - 2.5” with 0.5” holes|Ball
Ball- XL- Tiger Hard Plastic- All|Ball
Ball-10” - hard plastic|Ball
Ball-10” with 4” holes-hard plastic|Ball
Ball-12"- Red Jolly- Hard Plastic|Ball
Ball-14” with 4” holes-hard plastic|Ball
Ball-2.75”-Electronic squiggle|Ball
Ball-24”- Tiger Hard Plastic- Brown|Ball
Ball-6” with 1” holes- hard plastic|Ball
Ball-6” with 2” holes, hard plastic|Ball
Ball-6”-Romp n roll|Ball
Ball-7” with 3” holes- hard plastic|Ball
Ball-8.5” with 3” holes-hard plastic|Ball
Ball-8”-Romp n roll|Ball
Ball-Saurus Egg ( Green)- Tiger Hard Plastic|Ball
Ball-Saurus Egg- Tiger Hard Plastic|Ball
Ball-Shire|Ball
Ball-Soccer - 4.75”|Ball
Ball-Tug n toss - jolly|Ball
Ball-Ungulate|Ball
Bamboo platform|General
Bamboo stick|General
Bamboo wind chime|General
Barnyard Feces- Fresh|Biological
Basket - hanging|General
Basket - hanging -spiral|General
Basket - hearts- thin plastic|General
Basket - pumpkin with 7.5” opening- thin plastic|General
Basket feeder- Tortoise|General
Basket- pumpkin- standard-sized- thin plastic|General
Basket- Wicker - oval|General
Basket- Wicker - shallow-round|General
Basket- Wicker- large|General
Basket- Wicker- square with handle|General
Basket-pumpkin- huge, 9” opening- thin plastic|General
Bath - In approved Container|General
Bead Toy Hanging on Metal Wire|General
Bear rattle|General
Bedding from other animals|Biological
Bedding from other animals- non predator|Biological
Bells- sleigh|General
Bird of Prey diet ( BOP)|Food
Bird toys: any hanging toy with beads / wooden pieces / paper/wire/rope/metal|Range
Birdhouse gourd|General
Biscuit or biscuit powder( Browse, Leaf Eater, New World)|Food
Blood ( frozen or liquid)|Food
Bloodworms|Food
Blue bumpy hide- 2.5’|General
Bolted rubber bowls|General
Bone ( Knuckle Bones)|Food
Bones ( Soup bones)|Food
Bongo|General
Booda Dome top-7.25” hole|General
Boomerang feeders- rubber|General
Bottle- 1” hole- thin plastic|General
Bottle-1.75” hole- Metal|General
Bowl - 8-12”- hard plastic|General
Bowl - large - thin plastic|General
Bowl - Medium- neon- Hard Plastic|General
Bowl - wavy- large- thin plastic|General
Bowl -16”- thick rubber|General
Bowl -5-7”- Hard Plastic|General
Bowl- 2" or lager- Metal|Range
Bowl- 2" or larger- Hard Plastic|Range
Bowl- 6" or Larger- Metal|Range
Bowl- Any Size- thick rubber|Range
Bowl- Green- thin plastic|General
Bowl- Medium- Hard Plastic|General
Bowl-11”- thick rubber|General
Bowling balls - various weights|General
Bowling pins|General
Bread|Food
Brine Shrimp|Food
Broth ( chicken/ Beef)|Food
Broth ( vegetable)|Food
Browse Forest|General
Brush board|General
Brush head -9”|General
Brush head- Any|Range
Brush head-0.5” hole|General
Bubble Bath in approved container|General
Bubbles|General
Bucket - 3”- thin plastic|General
Bucket - thin plastic|General
Bucket -7”- metal|General
Bucket planter|General
Bucket- Holee- 5 Gallon|General
Buckets - 2”- thin metal|General
Buckets - 4”-metal|General
Buckets-Small Metal|General
Burlap bags|General
Burlap Sack with Shells|General
Bus bin- Thick Plastic|General
Busy board - locks|General
Busy board- lock and washer|General
Cake tin|General
Canned cat food|Food
Canned dog food|Food
Canned Marmoset Diet|Food
Canned Primate Zupreem|Food
Canoe paddle - small-hard plastic|General
Car wash strips|General
Cardboard (Boxes, Pieces, Egg Crates)|General
Cardboard Box- Thick|General
Cardboard Cat Scratcher Triangle|General
Cardboard Cat Scratcher- Balls must be removed before leaving it overnight|General
Cardboard tubes - All|General
Carrot Ball|Puzzle feeder
Cat ball track|General
Cat Ball tract with cardboard- Do not leave ball in overnight|General
Cat ball tract- Purple|General
Cat Toy Donut|General
Cat toys|General
Cat toys- hanging|General
Cereal|Food
Chair - kid sized- plastic|General
Chair Plastic- Orange|General
Chairs - adult- plastic|General
Chairs- kid sized- plastic/adult- plastic|Range
Chalk drawing|General
Cheese|Food
Chew - A|General
Chew - B|General
Chew - C|General
Chew - D|General
Chew - E|General
Chew - F|General
Chew A-G|Range
Chew rope toy|Chew Toy
Chew toy - Any|Range
Chew Toy ( wood, hemp, wire, shells, fire hose)|Chew Toy
Chew toy- Colorful cardboard hanger|Chew Toy
Chew toy- Grapevine balls|Chew Toy
Chew toy- Natural stick with wood splices|Chew Toy
Chew toy- Newspaper cube feeder with twine|Chew Toy
Chew Toy- Tongue Depressor Hut|Chew Toy
Chew toy- Wood and cork chews|Chew Toy
Chew toy- Wood Chew Paddle with Dangle Beads and Bells|Chew Toy
Chew toy- Wood Chew Towers Hanging with Bells|Chew Toy
Chew toy- Wood Chew- Hanging metal Skewer with Metal Rings and Beads|Chew Toy
Chew toy- Wood Chew- Hanging Metal Skewer, Plank and Balls w/Bell|Chew Toy
Chew toy- Wood Chew- Hanging Metal Skewer, Small Planks|Chew Toy
Chew toy- Wood Chew- Hanging on Twine Sticks and Balls|Chew Toy
Chew toy- Wooden blocks with 1” hole|Chew Toy
Chew toy- Wooden Chew Sticks and Beads|Chew Toy
Chew Toy-Coconut bead toy|Chew Toy
Chew Toy-Firehose Wooden Bead Spinner|Chew Toy
Chew toy-Hay Chew Ball|Chew Toy
Chew toy-Hay Rope Chew Ball|Chew Toy
Chew toy-Wicker ball - softball-sized|Chew Toy
Chew toy-Wood and shell hanger|Chew Toy
Chew toy-Wood Chew- Guinea Pig Blocks on Wood Skewer|Chew Toy
Chew toy-Wood Chew- Hanging Plastic Cord|Chew Toy
Chew toy-Wood Chew- Plankwood on Chain Hanging|Chew Toy
Chew toy-Wood Chew- Small Plank and Ball Hanging|Chew Toy
Chew toy-Wooden chew toy hanger|Chew Toy
Chew-G|General
Chey toy- Rope Chew|Chew Toy
Chicken - Whole|Food
Chicken Scratch|Food
Chicken Swing|General
Chicken/ Beef/ Horse Chunk|Food
Chicks|Food
Clam Tongue|Food
Climbing cargo net|General
Clothespins|General
Coconut and measuring cups hanger|General
Coconut bead toy|General
Coconut Bedding|General
Coconut half|General
Coconut shell hide|General
Coffee cans- plastic-hanging|General
Cool whip|Food
Cooling mats|General
Corks|General
Corrigated Pipe 6"to 8" Diameter|General
Cowbell-large|General
Cowbell-medium|General
Cowbells on metal chain|General
Crab|Food
Crackers|Food
Cream cheese|Food
Crickets|Food
Crispbread|Food
Critter Corner- Any|Range
Critter Corner-Large|General
Critter Corner-Small|General
Critter tube - giant elbow|General
Critter tubes - Any|Range
Critter tubes - giant|General
Critter tubes - small|General
Croc Gelatin- water, beef blood, beet juice, gelatin, whole prey from diet|Food
Crushed peppermint|Food
Cube and tubes-large|General
Cube-2.5” hole-hard plastic|General
Cupcake tin- Metal|General
Cups- Kids- Soft Plastic|General
Cutting board- Thick Plastic|General
Cuttlebone|General
Cylinder- 18”- Tiger Hard Plastic|General
Cylinder-12”- Tiger hard plastic|General
Daisy door matt|General
Deer|Food
Dice- 4.5”- hard plastic|General
Dig box: Approved container with approved substrate|General
Dishwasher basket - Munchkin|General
Dive ring-large|General
Doctor Office Toy- Small|General
Doctor’s office toy|General
Dogloo - hard plastic|General
Donut rings-4.5”- hard plastic|General
Donut-18”-tiger hard plastic|General
Double-ended snap hook|General
Double-loop chain|General
Drain Pan - 28” -hard plastic|General
Drain pan - large-metal|General
Drainage pipe -1.5” - thin plastic|General
Drainage tube -4.5”- thin plastic|General
Drawer organizer - hard plastic|General
Dri-decking|General
Dried Corn Husks|General
Drum- 55 gal- tiger hard plastic|General
Drying rack- hard plastic|General
Duckweed|Food
Dust Bath|General
Earthworms|Food
Easter eggs -thin plastic|General
Eggs ( scrambled, raw , frozen ( without shell), hard boiled)|Food
Equine Scratcher|General
Essential oil diffuser|General
Essential oils|General
Exercise ( Walks/ Floor Time)|General
Exercise saucer - 12”|General
Exercise wheel - 12” (various colors)|General
Exercise wheel - 8.5” (various colors)|General
Exercise wheel- armadillo|General
Fabric bag|Fabric
Fabric bag with mesh hole|Fabric
Fabric braided strips|Fabric
Fabric strip ball|Fabric
Fabric tunnel - long|Fabric
Fabric- Carpet Squares|Fabric
Fabric- cat nip plush|Fabric
Fabric- Cat tower|Fabric
Fabric- Critter Pouch|Fabric
Fabric- Fleece Liner with Pocket|Fabric
Fabric- Hammock - corner|Fabric
Fabric- Hanging|Fabric
Fabric- Hanging hammock|Fabric
Fabric- Outdoor cushion|Fabric
Fabric- Shoe organizer|Fabric
Fabric- Tunnel|Fabric
Fabric-Tunnel - foldable|Fabric
Fabric: Blankets, clothing( no buttons/ zippers), towels, burlap, pillow case- no loose strings|Fabric
Fabric: Burlap|Fabric
Fabric: fleece blankets|Fabric
Fan Frame - 24”|General
Faux plant|General
Faux plant and bamboo square|General
Feather duster|General
Feathers|Biological
Feeder fish|Food
Feeders- Lemurs Only|Puzzle feeder
Ferret condo - large|General
Ferret flexible tubes- thin plastic|General
Fetal pigs|Food
Figs- Fresh or dehydrated|Food
Firehose - braided browser|Firehose
Firehose - Large- 3 Block|Firehose
Firehose cube - rubber|Firehose
Firehose cube- fabric|Firehose
Firehose curtain - fabric|Firehose
Firehose donut platform - 20” fabric and hard plastic|Firehose
Firehose fabric pockets on wood panel|Firehose
Firehose fold - fabric-hanging|Firehose
Firehose hammock - 23” hanging- rubber|Firehose
Firehose hammock - hanging fabric|Firehose
Firehose hammock - rubber on PVC|Firehose
Firehose hammock - short fabric|Firehose
Firehose hammock hide|Firehose
Firehose hammock with sticks - rubber|Firehose
Firehose hammock- 16” hanging- fabric|Firehose
Firehose hanger - three blocks|Firehose
Firehose Heart|Firehose
Firehose Mat|Firehose
Firehose simple braid - fabric|Firehose
Firehose spiral|Firehose
Firehose square knot feeder - P-Hose|Firehose
Firehose square knot feeder - rubber or fabric|Firehose
Firehose triangle- 23”- Rubber|Firehose
Firehose tube bed|Firehose
Firehose- Hoops|Firehose
Fish (herring, capelin, silversides, shrimp, trout, smelt, mackerel)|Food
Flamingo - yard decor - thin plastic|Firehose
Fleece forest|Firehose
Floppy Fish- Supervised Only|General
Flour|Food
Flower pot -0.5” hole- thin plastic|Firehose
Flower pot hide - thin plastic|Firehose
Flower pot with small holes - thin plastic|Firehose
Foam tile|Firehose
Food coloring|General
Freezable Treat Holder|General
Frisbee - 5”- hard plastic|Firehose
Frisbee - 9” hard plastic|Firehose
Frisbee 9” stack - hanging|Firehose
Frisbee- hard plastic- any|Range
Frog Cup|General
Fruit Smoothies ( frozen or liquid)|Food
Fur/ Wool/ Fleece|Biological
Garden pipe - 10” - hard plastic|General
Garden pipe - 19” - Hard Plastic|General
Garden pipe - 8”- hard plastic|General
Garden pipe - short- hard plastic|General
Garden pipe exercise wheel|General
Garden pipe hide- Hard Plastic|General
Garden pipe smooth- Hanging- Hard Plastic|General
Garden pipe- 6.5”- hard plastic|General
Gas can - hard plastic|General
Gelatin/ Jell-O|Food
Goat's milk|Food
Grapevine wreath|General
Grave Stones|General
Half donut - hanging- large- hard plastic|General
Half wheel - 7”|General
Hammock - Blue|General
Hammock - canvas|General
Hammock Mat|General
Hammock Mat - Green|General
Hammock Zebra Print|General
Hammock- circular swing|Fabric
Hammock- Small Round Deep|Fabric
Hanging Silicone Flower Feeder|Puzzle feeder
Hard hats|General
Hay ball|General
Hay feeder - hanging 3.5” ball|General
Hay feeder - hanging 3” ball|General
Hay feeder - thin plastic- critter-sized|General
Hay feeder - wire ball|General
Hay feeder - wooden|General
Hay Roller|General
Herb container and rack|General
Herb container with top lid, easily removable|General
Hide -  two-story wooden tub|General
Hide - Croc|Hide
Hide - cut tub- thin plastic|Hide
Hide - elevated stick|Hide
Hide - half log|Hide
Hide - half pipe- PVC- large|Hide
Hide - igloo- thin plastic|Hide
Hide - log with half roof|Hide
Hide - Octopus Plush|Hide
Hide - PVC- half pipe|Hide
Hide - shark plush|Hide
Hide - small- hard plastic|Hide
Hide - tote- square hole- thin plastic|Hide
Hide - tote- thin plastic|Hide
Hide - TP|Hide
Hide - turtle plush|Hide
Hide - wooden|Hide
Hide - wooden cabin|Hide
Hide - wooden holey cube|Hide
Hide -tub- hard plastic|Hide
Hide with stairs|Hide
Hide- Cave Bed|Hide
Hide- Clear Plastic- Small|Hide
Hide- Cube and Tubes|Hide
Hide- Fish|Hide
Hide- Fish/ Turtle plush/ octopus plush/ shark plush/ croc|Range
Hide- Hammock with Fabric Strips|Hide
Hide- Hay Log|Hide
Hide- Plastic Shroom|Hide
Hide- Shark Tunnel|Hide
Hide- Wood Dome- small|Hide
Hide- Wooden House|Hide
Holiday Enrichment ( construction or wrapping paper, paint, safe glue, cardboard)|General
Holiday Enrichment ( Thick cardboard/ Paint)|General
Honey|Food
Hoof Trimmings - goat/ sheep/horse/ burror/|Biological
Hornbill Forage Tube|General
Ice|General
Ice cream|Food
Ice cream cones|Food
Ice mold - cake tins- metal|General
Ice mold - heart cupcake tin- metal|General
Ice mold - small- soft rubber|General
Ice mold - soft rubber|General
Ice mold- mini- hard plastic|General
Ice tray - hard plastic|General
Iceberg - 35” - Tiger hard plastic|General
Iceberg - giant- tiger hard plastic|General
Inflatable penguins|General
Insectivore diet|Food
Insects- dried/alive (crickets, mealworms, superworms, wax worms,beetles, cockroaches, ants)|Food
Jingle cat toy - small|General
Jolly apple - large- hard plastic|General
Jolly egg - 8” or 12”- hard plastic|General
Juice (dilute)|Food
Keeper Boots- soft rubber|General
Keg - standard sized -metal|General
Keg 23” - hard rubber|General
Ketchup|Food
Keyboard piano|General
Kibble- Cat|Food
Kibble- Dog|Food
Kiddie keys|General
Kong 3” -stuffable|Kong
Kong cat roller|Kong
Kong duets kibble ball|Kong
Kong Extremes - S (3”), M (3.5”), L (4”), XL (5”)- XXL (6”)|Range
Kong frog|Kong
Kong jumbler football|Kong
Kong jumbler toy|Kong
Kong Pull and Squeak|Kong
Kong roller wheel 6”|Kong
Kong squeezz balls|Kong
Kong stuff-a-ball 3”|Kong
Kong wobbler 8”|Kong
Kong- Chew King|Kong
Kong- Shell- Small|Kong
Kong- Treat Ring - Large Animal|Kong
Kong-12”-8lbs/5lbs|Kong
Kong-Shell- Large|Kong
Krill|Food
Kronk toy|General
Ladder - small -wooden|General
Ladder Collapsible|General
Laundry basket|General
Leaf Piles|Biological
Lick-it Boredom Buster|General
Likit Mounted|General
Likit refills|Food
Lily pad - Large- soft plastic|General
Lily pads - soft plastic, small|General
Little tykes playset|General
Little tykes- Slide- All|Range
Little tykes-Slide|General
Little tykes-Slide - curved|General
Little tykes-Slide - long green|General
Little tykes-Slide - yellow|General
Live crayfish|Food
Live plants|General
Log ( Rotten/ New)|General
Loofahs - natural|General
Looky-Lou 24in|General
Marble Box|General
Mazuri Gel Berry|Food
Mazuri Gum Arabic|Food
Mealworms|Food
Measuring Cup Bird Toy- metal- hard plastic|General
Measuring cups - hard plastic|General
Measuring spoons - hard plastic|General
Mega Blocks - large- Hard Plastic|General
Mega blocks - standard-sized- hard plastic|General
Megaphone - 18” -hard plastic|General
Milk crate- black- hard plastic|General
Milk crate- red- hard plastic|General
Mirror - kiddie|General
Mirror - parrot- hard plastic,hanging|General
Mirror hanger - small|General
Mirror tub - 5.5”|General
Mirror- Looking Bowl|General
Mirror- Looky Lou - 10.5” hanging- Hard Plastic|General
Mirror- Parrot- hard plastic, hanging/ kiddie|Range
Mirror-Rocky Lou 17”|General
Misting|General
Mixed nuts|Food
Mobile feeder|General
Mobile- wood and chain|General
Molasses|Food
Moss dried|Biological
Moving exhibit furniture|General
Music- make sure to turn off at night|General
Mysis Shrimp|Food
Nebraska meat|Food
Nori Dried Seaweed|Food
Nylon two-story tunnel|General
Oatmeal|Food
Oatmeal container|General
Organizers- hanging|General
Otter Float|General
Otter hardware|General
Packing peanuts - biodegradable|General
Paint (non-toxic)|General
Pallet - hard plastic|General
Pancake|Food
Paper products: newspaper, phone books, toilet paper, paper towels, packing paper, confetti, bags, construction paper, magazines ( no staples) , streamers, coffee filters, Paper mache, grain bags (no liners)|General
Pasta ( Uncooked or Cooked)|Food
Pasta (cooked)|Food
Pasture pal- hard plastic|General
Peanut butter|Food
Peanuts|Food
Peas: frozen|Food
Peg board|General
Pellet feeder fish toy|General
Pet bed - 12”|General
Pet bed - 22”|General
Pet bed - small-plush|General
Pet bed- 12"-22"/ small- plush|Range
Pet Bed- Donut|Fabric
Pet Bed- X small- Plush|Fabric
Pet tunnel|General
Pick board|General
Pill organizers|General
Pill-32”- Tiger Hard Plastic|General
Pinatas|General
Pine cones|Biological
Pipe builder toy|General
Platform- astroturf swinging|General
Playdough container|General
POLYETHYLENE TRAY|General
Poo- kiddie/ turtle|Range
Poo/- kiddie/ turtle|Food
Pool - kiddie|General
Pool - turtle|General
Popcorn|Food
Popsicle sticks|General
Pouch - small|General
Prima Rocker- 25”X12”- Hard Plastic|General
Prima Rocker- 31”X15in - Tiger Hard Plastic|General
Primate Ladder- Large|General
Primate Ladder- Small|General
Produce (no grapes/ raisins) (whole, chunked, smoothie, dried, dehydrated)|Food
Produce (whole, chunked, smoothie, dried, dehydrated)|Food
Projector|General
Pumice Stone Square|Chew Toy
Puzzle Feeder - 28”-Bamboo stick|Puzzle feeder
Puzzle feeder - bone|Puzzle feeder
Puzzle feeder - bone flap|Puzzle feeder
Puzzle feeder - Flip board dog game|Puzzle feeder
Puzzle Feeder - Hornbill Break Through ( Four 3in holes)|Puzzle feeder
Puzzle feeder - maze|Puzzle feeder
Puzzle feeder - paw flap|Puzzle feeder
Puzzle feeder - puzzle piece sliding|Puzzle feeder
Puzzle feeder - red paw|Puzzle feeder
Puzzle feeder - sliding circle|Puzzle feeder
Puzzle feeder - sliding paw|Puzzle feeder
Puzzle feeder - strategy game|Puzzle feeder
Puzzle feeder - treat balls|Puzzle feeder
Puzzle feeder - wheel|Puzzle feeder
Puzzle Feeder -Levels- Hard Plastic|Puzzle feeder
Puzzle Feeder ball- 4.5”-Treat dispenser|Puzzle feeder
Puzzle Feeder Ball- 4”-Treat dispenser|Puzzle feeder
Puzzle Feeder Ball-Treat dispensing - blue|Puzzle feeder
Puzzle feeder ball-Treat dispensing - carrots|Puzzle feeder
Puzzle Feeder- 7”- Trident|Puzzle feeder
Puzzle Feeder- Automatic treat dispenser|Puzzle feeder
Puzzle Feeder- Barnacle treat dispenser 3”|Puzzle feeder
Puzzle Feeder- Basket - Tortoise|Puzzle feeder
Puzzle Feeder- Bob-a-lot|Puzzle feeder
Puzzle Feeder- Busy buddy - egg dispenser|Puzzle feeder
Puzzle Feeder- Catit Tree|Puzzle feeder
Puzzle feeder- catit tube|Puzzle feeder
Puzzle Feeder- Coconut Hanging|Puzzle feeder
Puzzle Feeder- Coffee cans- Plastic- on branch- hanging|Puzzle feeder
Puzzle feeder- crumble feeder|Puzzle feeder
Puzzle Feeder- Dog tornados|Puzzle feeder
Puzzle Feeder- Dozzopet|Puzzle feeder
Puzzle Feeder- Firehose container|Puzzle feeder
Puzzle Feeder- Fleece Pocket|Puzzle feeder
Puzzle Feeder- Forage Cups|Puzzle feeder
Puzzle Feeder- Foraging Tray|Puzzle feeder
Puzzle Feeder- Green Spinning Feeder – Hard Plastic|General
Puzzle Feeder- Hanging Branch|Puzzle feeder
Puzzle Feeder- hanging lids|Puzzle feeder
Puzzle Feeder- Hay and Produce Log|Puzzle feeder
Puzzle Feeder- Hay Play|Puzzle feeder
Puzzle feeder- hide n slide|Puzzle feeder
Puzzle Feeder- Hol-ee Roller 3.5 in|Puzzle feeder
Puzzle Feeder- Hol-ee Roller 3.5in-8in|Range
Puzzle Feeder- Hol-ee Roller 5in|Puzzle feeder
Puzzle Feeder- Hol-ee Roller 8in|Puzzle feeder
Puzzle Feeder- Hol-ee treat ball|Puzzle feeder
Puzzle Feeder- Holee-roller extreme|Puzzle feeder
Puzzle Feeder- Honeycomb - 20” with 2” holes-hard plastic|Puzzle feeder
Puzzle Feeder- Honeycomb - 24” with 3.5” holes- Wooden|Puzzle feeder
Puzzle Feeder- Honeycomb - 8” half with 1” holes- Hard Plastic|Puzzle feeder
Puzzle Feeder- Honeycomb- 11” with 2” holes- hard plastic|Puzzle feeder
Puzzle Feeder- Jenga|Puzzle feeder
Puzzle Feeder- Jungle Jax 5 Leg|Puzzle feeder
Puzzle Feeder- Leaf Dish|Puzzle feeder
Puzzle Feeder- Likit-snak-ball|Puzzle feeder
Puzzle Feeder- Long Hanging Branch|Puzzle feeder
Puzzle Feeder- Magic Mushroom|Puzzle feeder
Puzzle feeder- Milk jug spinner|Puzzle feeder
Puzzle Feeder- Mod.|Puzzle feeder
Puzzle feeder- Otto-acrylic cylinder with 1” holes|Puzzle feeder
Puzzle feeder- parrot|Puzzle feeder
Puzzle Feeder- Petstages|Puzzle feeder
Puzzle Feeder- Platform and door|Puzzle feeder
Puzzle Feeder- PVC Cap|Puzzle feeder
Puzzle Feeder- PVC Hanging Reach Feeder|Puzzle feeder
Puzzle Feeder- Serval Tube|Puzzle feeder
Puzzle Feeder- Sleeve|Puzzle feeder
Puzzle Feeder- Snack catchers|Puzzle feeder
Puzzle Feeder- Spinning diet|Puzzle feeder
Puzzle Feeder- Teeter totter|Puzzle feeder
Puzzle Feeder- Three Wooden Block-Large|Puzzle feeder
Puzzle Feeder- Three Wooden Block-Medium|Puzzle feeder
Puzzle Feeder- Three Wooden Block-Small|Puzzle feeder
Puzzle Feeder- Trough Feeder|Puzzle feeder
Puzzle Feeder- Wobble cap PVC|Puzzle feeder
Puzzle Feeder-0.75” hole- Egg dispenser|Puzzle feeder
Puzzle Feeder-Activity boxes|Puzzle feeder
Puzzle Feeder-Amazing Graze with Cap|Puzzle feeder
Puzzle Feeder-Amazing Graze-Without Cap|Puzzle feeder
Puzzle Feeder-Baffle Cage|Puzzle feeder
Puzzle Feeder-Bamboo skewer|Puzzle feeder
Puzzle feeder-Bullet-hanging|Puzzle feeder
Puzzle Feeder-Flat circle with dips|Puzzle feeder
Puzzle Feeder-Hide, Seek & Treat|Puzzle feeder
Puzzle Feeder-Holee-roller oval|Puzzle feeder
Puzzle Feeder-Honeycomb-12” with 0.8” holes- Hard Plastic|Puzzle feeder
Puzzle feeder-PB jar board|Puzzle feeder
Puzzle Feeder-Rockin treat ball|Puzzle feeder
Puzzle Feeder-Rockin Treat Ball w/ Zip Tie|Puzzle feeder
Puzzle feeder-Treat N play bow tie-5”|Puzzle feeder
Puzzle feeder-Trex block hanger|Puzzle feeder
Puzzle Feeder-Tube- Tiger Hard Plastic|Puzzle feeder
Puzzle feeder-Tug-a-jug|Puzzle feeder
Puzzle feeder-Twist n Treat|Puzzle feeder
Puzzle feeder-Twist n Treat-Large|Puzzle feeder
Puzzle Feeder-Wooden box|Puzzle feeder
Puzzle Feeder-Wooden maze - with screws for cardboard insert|Puzzle feeder
Puzzle Feeders- Silverware racks|Puzzle feeder
PVC - 1” with knobs|PVC
PVC -0.5” holes- Curved|PVC
PVC -2” holes- assembled|PVC
PVC -XL tunnel|PVC
PVC Abacus|Puzzle feeder
PVC arches - large|PVC
PVC browse feeder|PVC
PVC Bungee|PVC
PVC connector - large|PVC
PVC cross - 1.25” holes|PVC
PVC double|PVC
PVC elbow hanger - small|PVC
PVC feeder gun|PVC
PVC hide - 12”- long|PVC
PVC honeycomb|PVC
PVC Honeycomb- small|PVC
PVC pipe hanger|PVC
PVC pipe with heavy insert|PVC
PVC pipe with moving shell|PVC
PVC pipes- three hanging|PVC
PVC Reach Feeder|PVC
PVC square 33”|PVC
PVC square feeder|PVC
PVC squares - 8”|PVC
PVC stack - hanging caps|PVC
PVC stack - hanging tubes|PVC
PVC T-shaped - large hanger|PVC
PVC with 0.25” holes|PVC
PVC with 0.25” holes - hanging|PVC
PVC with 0.3” holes|PVC
PVC with 0.5” holes - hanging|PVC
PVC with 1.5” hole|PVC
PVC with 2” holes|PVC
PVC with holes- hanging|PVC
PVC with large angled connector|PVC
PVC-2” holes- long|PVC
PVC-Rain stick|PVC
Quail|Food
Quail egg|Food
Quick Link|General
Rabbit heads/feet|Food
Rabbits (5 pounds or larger)|Food
Rabbits: small|Food
Radio flyer wagon|General
Raised pet bed|General
Rat tails|Food
Rattle pyramid|General
Rectangle Swing|General
Recycling bin - 10 gal.|General
Rice (cooked)|Food
Rock and fungi decor|General
Rocks - large-hard plastic|General
Rocks - small-painted|General
Rocks ( larger than golf ball )|General
Rodent- Guinea pigs|Food
Rodent- Pinkies|Food
Rodent- Rats|Food
Rodent-Mice|Food
Rodents (mice, rats, guinea pigs, pinkies, hoppers)|Food
Rope ladder - mini with sticks and twine|General
Rubber Ducks - small|General
Rubber Jax|General
Rubber mat with grooves|General
Rubber Post Scratcher|General
Salt Block Pan|General
Sand|General
Sand castle mold|General
Sand eels|Food
Saucer swing|General
Scallops|Food
Scatter Feed|General
Scent ( herbs, spices, extracts, perfume, lures, diluted mouthwash)|General
Scent ( herbs, spices, lures)|General
Scent ( Oils)|General
Scratch - n- All|General
Scratching post - rope wrapped cardboard tube|General
Scratching post - Rope-wrapped PVC - XL|General
Scratching post - turf wrapped PVC - hanging|General
Scratching Post- Small|General
Scratching Post- Walk Through|General
Scratching Post- Walk Through- Small|General
Sea toys|General
Sensory blocks|General
Shell Scrub|General
Shells - large|General
Shells - small|General
Shells on braided twine|General
Shoe lid box- thin plastic|General
Shredit hanger - small|General
Silicon green bumpy mat|General
Skewer - metal|General
Skewer- wooden- metal|General
Skewers- metal- long|General
Skewers- Wooden|General
Slide - PVC otter|General
Slinky - 4” dia.|General
Slope panel with 3.5” hole|General
Slow feeder - 5”|Slow Feeder
Slow feeder - 7” - maze|Slow Feeder
Slow feeder - bumpy|Slow Feeder
Slow Feeder - Crop Circle|Slow Feeder
Slow feeder - purple swirl|Slow Feeder
Slow feeder - single spiral|Slow Feeder
Slow feeder - spirals|Slow Feeder
Slow feeder - zig zag|Slow Feeder
Slow Feeder- 5”|Slow Feeder
Slow Feeder- All|Range
Slow Feeder- Any With No Rubber Base|Range
Slow Feeder- Large Purple Swirl|Slow Feeder
Slow Feeder-single spiral Large|Slow Feeder
Smear boards|General
Snack container - large- thin plastic|General
Snack Shack-18"|Hide
Snack Shack-24”- Hard Plastic|General
Snack Shack-36”- Hard Plastic|General
Snake shed|Biological
Snow|General
Snuffle mat|General
Snuffle mat - small|General
Soft blocks-1.5” - 5.5”|General
Sparkle box|General
Spinning bamboo release|General
Spinning bottle feeder|General
Spinning dispenser - small green|General
Spinning dispenser - small- clear|General
Spinning PVC release|General
Spiral hanger|General
Spiral twine and bell perch|General
Spool - Blue- Tiger Hard Plastic|General
Spool- Purple/Brown- Tiger Hard Plastic|General
Spoons on chain|General
Sprinklers|General
Squid|Food
Stacked wood hanger|General
Stainless Steel Bells|General
Standing chime|General
Star beads hanger|General
Sticks|General
Stock tank - 100 gal.- Hard Plastic|General
Stock tank - 300 gal.- Hard plastic|General
Stock tank - 50 gallon-hard plastic|General
Stock tank - 700 gal.- Metal|General
Stock tank- Hard Plastic- All|Range
Stuffed animals|General
Substrate Piles: hay, straw, shavings, mulch, soil, sand, peat moss, wood wool, coconut fiber|General
Suet feeder - 5” with square holes|General
Suet feeder - 8” with rectangle holes|General
Suet feeder - 9” with square holes|General
Suet feeder- All|Range
Swing - plastic and metal chain|General
Swing- skywild|General
Table - small- thin plastic|General
Tamarind Pods|Food
Tenrec Play Gym- Supervised Only|General
terracotta pots|General
Tetrahedron- Hard Plastic|General
Time in exercise enclosures|General
Time in other animal exhibits|General
Timothy hay|Food
Tipsy Tom- Tiger Hard Plastic|General
Tipsy Tom- Tiger Hard Plastic Large|General
Tire - 12.5”|General
Tire - 9.5”|General
Tire - standard|General
Tire - Tractor- Wide|General
Tire swing with PVC and chain|General
Tire- 4.5”|General
Tire- Tiger Hard Plastic|General
Tire- Tractor|General
Tote - large- thin plastic|General
Traffic cone - 7”- Thin Plastic|General
Traffic cone -30” -hard rubber|General
Traffic cone- 18”- Hard Rubber- Damaged top|General
Traffic cone- 18”-Hard Rubber|General
Traffic cone- 19”- Soft Rubber- Damaged top|General
Trash can - 23”-metal|General
Trash can - hard plastic- large|General
Trash can - hard plastic-20 gal.|General
Trash can lid - hard plastic- large|General
Trash can lid - metal|General
Trash can lid- metal/ hard plastic- large|Range
Trash can- 3 gallon|General
Tray - hard plastic|General
Tray - thin plastic|General
Tray - thin plastic lid with dip|General
Treat dispenser with blue sticks|General
Tree splice angle|Chew Toy
Tree tunnel - long|General
Tub - 13” -metal|General
Tub - 22” -metal|General
Tub with holes - rectangle|General
Tunnel-Thin Plastic|General
Turtle Ramp/ Arboreal Feeder|Puzzle feeder
Twigs- less than 1" diameter no longer than 12"|General
Underwater Mirror- Hard Plastic|General
Vet wrap|General
Visual items outside of fence (examples: remote control car, shower curtain, pinwheel, movie, stuffed animal)|General
Water Jug|Puzzle feeder
Water Turtle Pellet|Food
Weazel ball|General
Weeble -19”-Tiger Hard Plastic|General
Weeble- Tiger Hard Plastic- Green|General
Weeble-19”- Tiger Hard Plastic- Barn|General
Wheelbarrow top|General
Whisk - metal|General
Whisk and beads hanger|General
White noise|General
Whole Clams|Food
Windchime- Coconut and bamboo|General
Wiregate carabiner|General
Wood wool|General
Wooden beads and bell hanger|General
Wooden block with holes|General
Wooden block with holes - hanging|General
Wooden Climbing stick structure - hanging|General
Wooden dowels|General
Wooden platform - small|General
Wooden shapes hanger|General
Wooden Swing Ladder|General
Wooden-Abacus Counter-Large|Chew Toy
Yard Flamingo- Small|General
Yogurt (includes frozen yogurt)|Food
Yogurt drops|Food
Stacking Cups|Puzzle feeder
Fabric- Fleece Pockets|Fabric
Fabric- Fleece Pockets with loops|Fabric
Hide - Fabric - Orange Triangle|Hide
Ball- Jolly- Rubber|Ball
Pumpkin|Food
Watermelon|Food
Produce ( Apple- corred) Cucumber, Pear ( coored) , Carrot, Celery, All Lettuces, Sweet Potato, Beet, Turnip, Squashes, Banana, Melon, Pineapple|Food
Flat fish|
Gel Clams|
Gel Window Clings|
Laser Pointer|
Resin gems|
Stone hideouts|
terracotta pot- broken|
Underwater dive shark|
underwater fun balls|
underwater fish rings|
underwater playstick|
Ball- Sensory Metal - Any|
Scratching Post- Cati|
Goat Hair, Equine Hair, Bunny Hair|
Adult brine (Artemia sp. >48 hrs old)|
Bell peppers (any color)|Food
Broccoli|Food
Cantaloupe|Food
Coconut|Food
Collard greens|Food
5 Gallon Water Jug|
Butter lettuce|
Forage ball- hard|
Gel clams (not approved for Marbles)|
Grapevine- nest|
Leaf dish- short|
Lily pad|
Puzzle feeder- Barnacle treat dispenser 6"|
Tray- Blue Fish|
Turtle Brush, Grey|
Snuffle Ball - Small- Large|
Silicon Hay Feeder|
Firehose Ladder|
Salt Block|
Coarse Salt|
Snake activity board- Make sure it cannot fall|
paper mache|
Produce Forage Board|
Puzzle Feeder- Slow release PVC feeder|
PVC Burrow Hide|
Dive Bell|
Wooden Dowel Bridge|
Ball- Wobble- Tiger Hard Plastic|
Puzzle Feeder- Hardwood Small|
Hide- Large Box|
Puzzle Feeder- Double Cone|
Runt Run|
Mushrooms|
Cat Exercise Wheel-Cat House|
Cat Exercise Wheel-Ambassador|
Puzzle Feeder - Teamwork Box|
Bell - Heavy Duty|
Fabric- Boa-Fleese- Climber|
Hammock- Rectangle|
Hanging Luna Ball|
Hanging Pinecone Forager|
Hide- Hanging Sphere 24in|
Hide- Hanging Sphere 18in|
Kong- Star Pod|
Pinecone Feeder|
Puzzle Feeder- PVC Tube Feeder Hanging|
Puzzle Feeder Ausse Dog Ball|
Puzzle Feeder- Hay Saver|
Puzzle Feeder- PVC Treat Tube|
Rabbit Relaxer|
Wood Primate Swing 15in|
Wood Primate Swing 24in|
BAll- Jolly- Stall Snack|
Firehose Sausage|
Puzzle Feeder- Ladels on a Chain|
Teeter Totter|
Bint Ladder|
Puzzle Feeder- Water Jug Spinning Feeder|
Christmas Tree|
Ball- Small Bouy- .5in hole|
Ball- Large Yellow Buoy- 2in hole|
Cat Scratch Ramp|
Puzzle Feeder Fun Board|
Puzzle Feeder- Hanging Clip Feeder|
Puzzle Feeder WindMill ( without caps)|
Puzzle Feeder Windmill ( with caps)|
Brush- Corner Mount|
Brush- Corner Mount- Mounted|
Jam|
Mustard|
Marshmallow/ Marshmallow Fluff|
Fit- Bone|
Cardboard Chips For Bedding|
Puzzle Feeder- Ball- Hard Plastic with Holes- Yellow|
Puzzle Feeder- Bamboo Basket|
PVC Holder and Cup Flamingo Feeder|
Puzzle Feeder- Blue Barrel Tiger Feeder|
Magnetic Tiles|
String Wand|
Puzzle Feeder - Hanging Board with Plastic Containers|
Stake In Bird Bath|
Giant Cat Ball Track - Tiger|
Snuffle ball- Crinkle|
Dog Bed - grey polyester|
Real Fur Pillow|
Snuffle Mat- Pond Theme|
Pet Bed >25in Plush|
Hide- Yellow Elephant|
Hide- All ( Small Animal Fabric Hide)|
Mortorized Cat Toy|
Feather Duster|
Puzzle Feeder- reptile cricket feeder|
Puzzle Feeder- Spinning Tube|
Tire - 6"|
Tire - 16"|
Ball - Noise Maker- Hard Plastic|
Buoy - Black - Hard Plastic|
Ball- Small Bouy- double .5in hole|
Buoy - Black -double loop -  Hard Plastic|
Buoy - Orange- Triple Loop- Hard Plastic|
Buoy - Brown- Single Loop- Hard Plastic|
Buoy - Pink and Orange- Douple Loop- Hard Plastic|
Hard Plastic Hanging Pouch|
Spinning Cat Laser|
Cat Activity Tree|
Paper Bedding|
Tunnel Scratcher|
Ball- Shake and Laugh|
Plush Toy-Tiny|
Chuckit Ball- Small|
Silicone Mat Grey - Thick|
Silicone Mat Blue- Thin|
Black 18" Giant Hard Plastic Elbow|
Black Hard Plastic Elbow|
Flamingo Floating Feeder Bowl|
Cat Tower- Large Cati|
Fabric- Busybody Blankie|
Nomad Matting|
Broadcast feed of pelleted diet in the holding room pool|
Tube- Green|
Weeble-XL Tiger Hard Plastic|
Catnip Ball|
Puzzle Feeder- Circle Pawslide|
Chinchilla Hut|
Puzzle Feeder- Firehose Wooden Post Browser|
Puzzle Feeder|
Pet Tunnel- T Shape|
Bunny Hut|
Reptile Hammock - Large and Small|
Puzzle Feeder- Dog Cold Treat Dispenser|
Jumping Post- On Serval Exhibit|
Ball- 22in- Orange- Tiger Hard Plastic|
Ball- Saurus Egg- Hanging- 2in holes- Hard Plastic|
Ball Pit Ball- Small- Hard Plastic|
Puzzle Feeder- Interactive Cat Toy|
Ball- 10in- Tiger Hard Plastic|
Hammock – Hanging – 14in – Mesh – Nylon Straps|
Mirror – Hanging Chain – 5in – Round – Metal|
Rubber – Spiral|
Hanging Rubber – Spiral – Chain|
Hanging Plastic – Double Disc – Firehose Straps|
Ball – 6in – 1in Holes – Hard Plastic|
Ball – Hanging Chain – 6in – 1in Holes – Hard Plastic|
Ball – Flat-Sided Saurus Egg – Hard Plastic|
Dog Toy – Interlocking Rings – Small – Rubber|
Heavy Duty Mirror|
"""


class Command(BaseCommand):
    help = 'Preload the master enrichment item catalog (name + category) from Master List Template.pdf'

    def handle(self, *args, **options):
        unknown, _ = ItemCategory.objects.get_or_create(name='Unknown')
        category_cache = {}
        created = 0
        already_existed = 0

        for line in ITEMS_TEXT.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            name, _, category_name = line.partition('|')
            name = name.strip()
            category_name = category_name.strip()

            if category_name:
                if category_name not in category_cache:
                    category_cache[category_name], _ = ItemCategory.objects.get_or_create(name=category_name)
                category = category_cache[category_name]
            else:
                category = unknown

            _, was_created = Enrichment.objects.get_or_create(name=name, defaults={'category': category})
            created += int(was_created)
            already_existed += int(not was_created)

        self.stdout.write(self.style.SUCCESS(f'Enrichment items: {created} created, {already_existed} already existed.'))
