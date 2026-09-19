"""
One-time (but re-runnable) preload of "Animal Behavior Master List.pdf" into
Division / String / TrainingAnimal / Behavior / Reinforcer / keeper accounts.

Transcribed by hand from a PDF export of a Google Sheet with two tabs,
Terrestrial and Aquatic. See the conversation this was built in for the
column-mapping decisions:
  - col A = string name (leading "*" stripped) + the keeper roster listed
    beneath it in the same cell
  - col B (Zims #) ignored
  - col C = species + individual name -> becomes the TrainingAnimal name
  - Terrestrial only: "Primary Trainer" -> stored as a note on the TrainingAnimal
    (no dedicated field for it yet)
  - Maintenance Behaviors / New Behaviors / Reinforcers -> imported
  - Aquatic-only "Active Training" and "Timeline" columns ignored
  - keeper roster placeholders "Intern"/"Docent"/"Volunteer"/"Terrestrial
    Staff" get real accounts; "Other" does not
  - "Bethany" and "Hannah" appear in both rosters but are two different
    people -> split into bethany1/bethany2, hannah1/hannah2 (Terrestrial=1,
    Aquatic=2); rename the usernames later once last names are known

Two animals were fully struck through in the source (apparently
retired/deceased) and are skipped: Tenrec-Nancy, Rabbit-American Lop/Timothy.

Run with: python3 manage.py import_animal_behavior_master_list
"""
import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from zoo.models import Behavior, Division, Reinforcer, String, TrainingAnimal

PASSWORD = '1957'
SPLIT_NAMES = {'Bethany', 'Hannah'}
SKIPPED_ASGS = {'Tenrec-Nancy', 'Rabbit-American Lop, Timothy'}


def a(name, trainer=None, maint=(), new=(), reinf=()):
    return {'name': name, 'trainer': trainer, 'maint': list(maint), 'new': list(new), 'reinf': list(reinf)}


TERRESTRIAL_KEEPERS = [
    'Carolyn', 'Maranda', 'Megan', 'Brittany', 'Mike', 'Laura', 'Nickey', 'Dakota', 'Audrey',
    'Darcie', 'Bekah', 'Jen', 'Bethany', 'Madeline', 'Chloe', 'Ian', 'Hannah', 'Intern', 'Docent', 'Other',
]

AQUARIUM_MAMMAL_KEEPERS = [
    'Lyssa', 'Bethany', 'Quinton', 'Macy', 'Rachel', 'Hannah', 'Sarah R', 'Sarah H', 'Lily',
    'Morgan S', 'Morgan P', 'Elizabeth', 'Thom', 'Kristal', 'Intern', 'Volunteer', 'Terrestrial Staff', 'Other',
]

AQUARIUM_OTHER_KEEPERS = [
    'Lyssa', 'Bethany', 'Quinton', 'Macy', 'Rachel', 'Hannah', 'Sarah R', 'Sarah H', 'Lily',
    'Morgan S', 'Morgan P', 'Elizabeth', 'Intern', 'Volunteer', 'Terrestrial Staff', 'Other',
]

DIVISIONS = {
    'Terrestrial': [
        {
            'name': 'Tiger/ Wolf String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Tiger-Sumatran, Raza', 'Maranda S.',
                  ['Target', 'Up', 'Down', 'Hand', 'Station', 'Scale', 'Follow', 'Sit', 'Touch', 'Shift'],
                  ['Hip poke', 'Tail', 'Emergency Recall', 'other hand'],
                  ['Chunk Horse Meat', 'Chicken Breast', 'Deer', 'Goats Milk', 'Whole Prey', 'Other']),
                a('Tiger-Sumatran, Rocky', 'Maranda S.',
                  ['Round About', 'Target', 'Up', 'Down', 'Hand', 'Station', 'Follow', 'Sit', 'Hip', 'Scale',
                   'Touch', 'Tail', 'Poke', 'Blood Draw'],
                  ['Other Hand', 'Open Mouth', 'Emergency Recall'],
                  ['Chunk Horse Meat', 'Chicken Breast', 'Deer', 'Goats Milk', 'Whole Prey', 'Other']),
                a('Tiger-Sumatran, Nety', 'Maranda S.',
                  ['Target', 'Station', 'Up', 'Down', 'Sit'],
                  ['Shift', 'Follow', 'Touch', 'Poke', 'Emergency Recall', 'Hand', 'Other Hand', 'Ultrasound Station'],
                  ['Chunk Horse Meat', 'Chicken Breast', 'Deer', 'Goats Milk', 'Whole Prey', 'Other']),
                a('Wolf-Maned, Guapa', 'Laura F.',
                  ['Target', 'Scale', 'Station', 'Squeeze', 'Up', 'Shift', 'Crate', 'Follow', 'Hold', 'Belly Touch'],
                  ['Poke', 'Arm Chute', 'Hand', 'Other Hand', 'Open Mouth', 'Touch Arm', 'Touch Hip', 'Down'],
                  ['Whole Prey', 'Goats Milk', 'Other']),
                a('Wolf-Maned, Ferdinand', 'Laura F.',
                  ['Up', 'Target', 'Hand', 'Station', 'Scale', 'Shift'],
                  ['Follow', 'Touch', 'Hold', 'Crate', 'Squeeze', 'Arm Chute', 'Other Hand', 'Open Mouth'],
                  ['Whole Prey', 'Goats Milk', 'Other']),
                a('Panda-Red, Taiji', 'Laura F.',
                  ['Station', 'Up', 'Hold', 'Target', 'Scale', 'Touch', 'Shift', 'Ear', 'Squeeze', 'Crate',
                   'Follow', 'Poke', 'Chute', 'Tail', 'Blood Draw'],
                  ['Hand', 'Open', 'Mask'],
                  ['Grapes', 'Apple', 'Bamboo', 'Other']),
                a('Panda- Red, Madeline', 'Laura F.',
                  ['Shift', 'Station', 'Up', 'Target', 'Touch', 'Crate', 'Ultrasound', 'Follow', 'Belly', 'Ear',
                   'Tail', 'Poke', 'Blood Draw', 'Chute', 'Hand'],
                  ['Other Hand', 'Come'],
                  ['Grapes', 'Apple', 'Bamboo', 'Other']),
            ],
        },
        {
            'name': 'Lemur String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Cat-Fishing, Mako', 'Megan H.',
                  ['Hand', 'Other Hand', 'Up', 'Down', 'Target', 'Squeeze', 'Crate', 'Scale', 'Recall', 'Sit'],
                  ['Open', 'Chute', 'Touch', 'Poke', 'Hold'],
                  ['Fish', 'Shrimp', 'Chunk Horse Meat', 'Chicken Breast', 'Whole Prey', 'Goats Milk', 'Other']),
                a('Cat-Fishing, Tallulah', 'Megan H.',
                  ['Hand', 'Other Hand', 'Up', 'Down', 'Target', 'Squeeze', 'Crate', 'Scale', 'Recall', 'Sit'],
                  ['Open', 'Chute', 'Touch', 'Poke', 'Hold'],
                  ['Fish', 'Shrimp', 'Chunk Horse Meat', 'Chicken Breast', 'Whole Prey', 'Goats Milk', 'Other']),
                a('Lemur-Red-ruffed, Carina', 'Megan H.',
                  ['Touch', 'Target', 'Up', 'Hand', 'Scale', 'Chute', 'Spin', 'Down', 'Here', 'Poke', 'Squeeze',
                   'Hang', 'Injection'],
                  ['Open', 'Crate', 'Other Hand', 'Poke', 'Station'],
                  ['Fruit', 'Other']),
                a('Lemur-Red-ruffed, Jude', 'Megan H.',
                  ['Touch', 'Target', 'Up', 'Down', 'Here', 'Hang', 'Spin', 'Scale', 'Hand'],
                  ['Other Hand', 'Poke', 'Crate', 'Squeeze', 'Injection', 'Open', 'Chute', 'Station'],
                  ['Fruit', 'Other']),
                a('Lemur-Ring-tailed, Rocky', 'Megan H.',
                  ['Target', 'Station', 'Up', 'Scale', 'Here', 'Spin'],
                  ['Crate', 'Squeeze', 'Touch', 'Down', 'Hold', 'Hand', 'Chute', 'Poke'],
                  ['Fruit', 'Other']),
                a('Lemur-Ring-tailed, Royce', 'Megan H.',
                  ['Target', 'Station', 'Up', 'Scale', 'Here'],
                  ['Crate', 'Squeeze', 'Spin', 'Touch', 'Down', 'Hold', 'Hand', 'Chute', 'Poke'],
                  ['Fruit', 'Other']),
                a('Lemur Troop', 'Megan H.', ['Station', 'Scale', 'Shift'], [], ['Fruit', 'Other']),
                a('Cat- Sand, Amir', 'Megan H.',
                  ['Scale', 'Target', 'Shift', 'Sit', 'Up', 'Down', 'Spin', 'Chute', 'Hand', 'Other Hand',
                   'Crate', 'Squeeze', 'Touch', 'Poke', 'Station', 'Recall', 'Hold'],
                  [], ['Whole Prey', 'Nebraska']),
                a('Cat- Sand, Jabari', 'Megan H.',
                  ['Scale', 'Target', 'Shift', 'Sit', 'Up', 'Down', 'Spin', 'Chute', 'Hand', 'Other Hand',
                   'Crate', 'Squeeze', 'Touch', 'Poke', 'Station', 'Recall', 'Hold'],
                  [], []),
                a('Fennic Fox, Gizmo', 'Megan H.',
                  ['Target', 'Crate', 'Scale', 'Sit', 'Recall', 'Tunnel', 'Shift', 'Chute', 'Hand', 'Other Hand',
                   'Up', 'Down'],
                  [], []),
                a('Serval, Kira', 'Megan H.',
                  ['Target', 'Up', 'Down', 'Sit', 'Station', 'Scale', 'Shift', 'Recall', 'Crate', 'Squeeze', 'Hand'],
                  ['Hip', 'Poke', 'Jump', 'Open', 'Hold', 'Chute'],
                  ['Whole Prey', 'Nebraska', 'Horse Chunk Meat', 'Chicken Breast', 'Other']),
                a('Serval, Tut', 'Megan H.',
                  ['Target', 'Up', 'Down', 'Sit', 'Station', 'Scale', 'Shift', 'Recall', 'Crate', 'Squeeze', 'Hand'],
                  ['Hip', 'Poke', 'Jump', 'Open', 'Hold', 'Chute'],
                  ['Whole Prey', 'Nebraska', 'Horse Chunk Meat', 'Chicken Breast', 'Other']),
                a('Serval, Ramona', None, ['Target', 'Scale', 'Crate', 'Squeeze', 'Up', 'Down', 'Paw', 'Sit'], [], []),
                a('Serval, Beatrice', None, ['Target', 'Scale', 'Crate', 'Squeeze', 'Up', 'Down', 'Paw', 'Sit'], [], []),
                a('Radiated Tortoise, Quint', 'Maranda', ['Target'], ['Recall'], ['Greens', 'Diet', 'Other']),
                a('Radiated Tortoise, Brody', 'Maranda', ['Target'], ['Recall'], ['Greens', 'Diet', 'Other']),
                a('Radiated Tortoise, Hooper', 'Maranda', ['Target'], ['Recall'], ['Greens', 'Diet', 'Other']),
            ],
        },
        {
            'name': 'Hippo / Okapi String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Hippo-Pygmy, Holly', 'Mike M.',
                  ['Target', 'Shift', 'Recall', 'Station', 'Scale', 'Touch', 'Ultrasound'],
                  ['Down', 'Poke', 'Foot', 'Mouth Manipulation', 'Squeeze', 'Blood Draw', 'Injection'],
                  ['Greens', 'Produce', 'Diet', 'Other']),
                a('Hippo-Pygmy, Ralph', 'Mike M.',
                  ['Target', 'Shift', 'Recall', 'Station', 'Scale', 'Touch', 'Open'],
                  ['Ultrasound', 'Nose Drops', 'Teeth', 'Poke', 'Follow', 'Target Pole', 'Station', 'Side Present',
                   'Squeeze', 'Blood Draw', 'Injection'],
                  ['Greens', 'Produce', 'Diet', 'Other']),
                a('Hippo-Pygmy, Huckleberry', 'Mike M.',
                  ['Target', 'Scale', 'Poke', 'Mouth Manipulation', 'Squeeze', 'Blood Draw', 'Injection', 'Down', 'Foot'],
                  [], ['Greens', 'Produce', 'Diet', 'Other']),
                a('Cassowary-Southern Dodo', 'Mike M.', ['Target', 'Station', 'Scale', 'Shift'],
                  ['Squeeze', 'Poke', 'Injection'], ['Fruit', 'Other']),
                a('Cassowary-Southern Moana', 'Mike M.', ['Target', 'Station', 'Scale', 'Shift'],
                  ['Squeeze', 'Poke', 'Injection'], ['Fruit', 'Other']),
                a('Okapi, Bakari', 'Nickey P.',
                  ['Desense', 'Scale', 'Ear Manipulation', 'Station', 'Touch', 'Blood Draw', 'Target', 'Poke'],
                  ['Injection', 'Radiograph', 'Ultrasound', 'Open Mouth', 'Foot', 'Back Up', 'Chute', 'Eye', 'Light'],
                  ['Browse', 'Other']),
                a('Hornbill-Ground, Hermione', 'Nickey P.', ['Shift', 'Station', 'Tap Target'],
                  ['Swallow', 'Come', 'Crate', 'A to B', 'Spin', 'Wing Lift'], ['Whole Prey', 'Nebraska', 'Other']),
                a('Flamingo-Caribbean, Yellow-Yellow; 2040', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Red-Black; 2049', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Orange-Orange; 2074', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Orange-Yellow; 2006', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Purple-Black; 2075', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Purple; 2053', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Green-Purple; 2078', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Blue; 2016', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Black-Black; 2011', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Red-Yellow; E291', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Amigo #69', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Hobbles #50', 'Nickey P.', ['Shift'], ['Scale', 'Hand Feed', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, #93', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Carl #86', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Amanda Blu- Yellow', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo-Caribbean, Elton Red - Orange; 2081', 'Nickey P.', ['Shift'], ['Scale', 'Isolate'], ['Krill', 'Diet', 'Other']),
                a('Flamingo, Entire Flock', 'Nickey P.', ['Shift'], ['Scale', 'Feeder Cup', 'Isolate'], ['Krill', 'Diet', 'Other']),
            ],
        },
        {
            'name': 'Fossa (was Gibbon) String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Binturong, Mee-Noi', None,
                  ['Target', 'Up', 'Down', 'Touch', 'Hand', 'Other Hand', 'Scale', 'Station', 'Chute'],
                  ['Crate', 'Squeeze', 'Poke', 'Recall', 'Tail Touch'], ['Grapes', 'Banana', 'Diet', 'Other']),
                a('Binturong, Susan', None,
                  ['Up', 'Down', 'Target', 'Station', 'Scale', 'All The Way', 'Belly Touch', 'Shift', 'Chute', 'Crate'],
                  ['Hand', 'Other Hand', 'Poke', 'Recall'], ['Grapes', 'Banana', 'Diet', 'Other']),
                a('Monkey-Black Howler, Abby', None,
                  ['Up', 'Down', 'Hand', 'Other Hand', 'Station', 'Scale', 'Squeeze', 'Shift', 'Door', 'Foot',
                   'Belly', 'Target'],
                  ['Open Mouth', 'Manipulate', 'Syringe'], ['Grapes', 'Figs', 'Diet', 'Other']),
                a('Monkey-Black Howler, Rocko', None,
                  ['Up', 'Down', 'Hand', 'Other Hand', 'Station', 'Scale', 'Shift', 'Door', 'Target'],
                  ['Open Mouth', 'Target', 'Squeeze', 'Syringe'], ['Grapes', 'Figs', 'Diet', 'Other']),
                a('Gibbon-Javan, Leon', None,
                  ['Hand', 'Foot', 'Target', 'Mouth', 'Station', 'Up', 'Down', 'Door', 'Shift', 'Scale', 'Hold',
                   'Hip', 'Touch', 'Target Hold', 'Hand Hold', 'Foot Touch'],
                  ['Syringe Injection', 'Squeeze', 'Poke', 'Open Mouth', 'Arm Chute'], ['Fruit', 'Other']),
                a('Gibbon-Javan, Isabella', None,
                  ['Hand', 'Foot', 'Belly', 'Mouth', 'Up', 'Down', 'Target', 'Scale', 'Door', 'Station', 'Shift',
                   'Touch', 'Belly Touch', 'Foot Touch', 'Hand Hold'],
                  ['Injection', 'Squeeze', 'Hold', 'Hip', 'Open Mouth', 'Target Hold', 'Arm Chute'],
                  ['Fruit', 'Other']),
                a('Fossa, Jeff', None,
                  ['Target', 'Up', 'Down', 'Follow', 'Shift', 'Chute', 'Scale', 'Touch', 'Poke', 'Hand'],
                  ['Crate', 'Other Hand', 'Lay', 'Inject'],
                  ['Deer', 'Chunk Horse Meat', 'Whole Prey', 'Chicken Breast', 'Other']),
            ],
        },
        {
            'name': 'Barn Ambassador',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Burro-Miniature, Crick', 'Brittany J.',
                  ['Target', 'Station', 'Open Mouth', 'Hold', 'Backup', 'Racking Up', 'Walk'],
                  ['Blood Draw', 'Scale', 'Halter', 'Recall', 'Touch', 'Ear Touch', 'Halter Target'],
                  ['Carrots', 'Celery', 'Apples', 'Grain', 'Other']),
                a('Burro-Miniature, Watson', 'Brittany J.',
                  ['Target', 'Station', 'Open Mouth', 'Hold', 'Backup', 'Racking Up', 'Walk'],
                  ['Blood Draw', 'Scale', 'Halter', 'Recall', 'Touch', 'Ear Touch', 'Halter Target'],
                  ['Carrots', 'Celery', 'Apples', 'Grain', 'Other']),
                a('Chicken-domestic Speckled Sussex, Blanche', 'Darcie H.', ['Recall', 'Crate'],
                  ['Touch', 'Shape Target'], ['Mealworms', 'Grain', 'Produce', 'Other']),
                a('Chicken-domestic Dominque, Janice', 'Darcie H.', ['Recall', 'Crate', 'Shape Target'],
                  ['Touch'], ['Mealworms', 'Grain', 'Produce', 'Other']),
                a('Chicken-domestic Easter Egger, Cady', 'Darcie H.', ['Recall'],
                  ['Crate', 'Touch', 'Shape Target'], ['Mealworms', 'Grain', 'Produce', 'Other']),
                a('Chicken-domestic Buckeye, Karen', 'Darcie H.', ['Recall'],
                  ['Crate', 'Touch', 'Shape Target'], ['Mealworms', 'Grain', 'Produce', 'Other']),
                a('Goat-Nubian, Ollie', 'Darcie H.', ['Scale'], ['Walk', 'Halter', 'Target'],
                  ['Grain', 'Produce', 'Other']),
                a('Goat-Oberhasli, Yodel', 'Darcie H.', ['Scale', 'Walk', 'Halter', 'Target'], [],
                  ['Grain', 'Produce', 'Other']),
                a('Goat, Leory', 'Darcie H.', ['Scale'], ['Walk', 'Halter', 'Target'], []),
                a('Goat, Willie', 'Darcie H.', ['Scale'], ['Walk', 'Halter', 'Target'], []),
                a('Goat-Boer, Tank', 'Darcie H.', ['Scale'], ['Walk', 'Halter', 'Target'], []),
                a('Goat-Boer, Frosty', 'Darcie H.', ['Scale'], ['Walk', 'Halter', 'Target'], []),
                a('Horse-Miniature, Noel', 'Darcie H.', ['Scale', 'Racking-up', 'Halter', 'Target'], ['Walk'],
                  ['Grain', 'Produce', 'Other']),
                a('Horse-Miniature, Tigger', 'Darcie H.', ['Scale', 'Halter', 'Racking-up', 'Target'], ['Walk'],
                  ['Grain', 'Produce', 'Other']),
                a('Sheep-Barbados, Lavender', 'Darcie H.', ['Scale', 'Target'], [], ['Grain', 'Produce', 'Other']),
                a('Sheep-Gulf Coast Native, Mitchell', 'Darcie H.', ['Scale', 'Target'], [],
                  ['Grain', 'Produce', 'Other']),
                a('Sheep-Gulf Coast Native, Ricky', 'Darcie H.', ['Scale', 'Target'], [],
                  ['Grain', 'Produce', 'Other']),
            ],
        },
        {
            'name': 'Komodo String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Tortoise-Aldabra, Jack', 'Audrey N.', ['Target', 'Scale', 'Poke', 'Color Discrimination'],
                  ['Foot'], ['Greens', 'Fruit', 'Veggie', 'Other']),
                a('Tortoise- Aldabra, Traveler', 'Audrey N.', ['Target', 'Scale', 'Poke', 'Color Discrimination'],
                  ['Foot'], ['Greens', 'Fruit', 'Veggie', 'Other']),
                a('Dragon- Komodo, Hannibal', 'Audrey N.',
                  ['Recall', 'Station', 'Scale', 'Shift', 'Target', 'Squeeze', 'Touch', 'Poke'], ['Palpate'],
                  ['Whole Prey', 'Chunk Horse Meat', 'Chicken Breast', 'Other']),
                a('Galapagos Tortoise, Ceaser', None,
                  ['Recall', 'Station', 'Scale', 'Shift', 'Target', 'Touch'], [], ['Celery', 'Diet']),
                a('Galapagos Tortoise, Martha', None,
                  ['Recall', 'Station', 'Scale', 'Shift', 'Target', 'Touch'], [], ['Celery', 'Diet']),
                a('Galapagos Tortoise, Beagle', None,
                  ['Recall', 'Station', 'Scale', 'Shift', 'Target', 'Touch'], [], ['Celery', 'Diet']),
            ],
        },
        {
            'name': 'Ambassador Reptiles/ Amphibian/ Inverts',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Turtle- Eastern Box, Jane', 'Jen D.', ['Target'], ['Crate', 'Station'],
                  ['Mealworms', 'Produce', 'Other']),
                a('Turtle- Eastern Box, Jill', 'Jen D.', ['Target'], ['Crate', 'Station'],
                  ['Mealworms', 'Produce', 'Other']),
                a('Turtle- Eastern Box, Jack', None, ['Station', 'Target'],
                  ['Scale', 'Crate', 'Color Discrimination'], ['Mealworms', 'Produce', 'Other']),
                a('Tarantula-Mexican Red Knee, Rosa', None, ['Crate'], [], ['Other']),
                a('Tarantula-Curly Hair, Harriet', None, [], [], []),
                a('Skink- Prehensile Tailed, Pup', 'Audrey N.', ['Target', 'Station', 'Presentation', 'Crate'],
                  [], ['Produce', 'Other']),
                a('Skink- Prehensile Tailed, Makira', 'Audrey N.', ['Station', 'Target', 'Presentation'],
                  ['Desensitizing'], ['Produce', 'Other']),
                a('Rat Snake-Black, Panther', 'Audrey N.', [], ['Shift'], ['Whole Prey', 'Other']),
                a('Corn Snake, Maizie', None, ['Station', 'Shift'], [], ['Whole Prey', 'Other']),
                a('Corn Snake, Cornflakes', None, ['Station', 'Shift'], [], ['Whole Prey', 'Other']),
                a('Frog-Dart- Y&B Poison, Amor', None, [], [], []),
                a('Uromastyx, Tazo', None, ['Target', 'Crate'], ['Station'], ['Lentils', 'Produce', 'Diet', 'Other']),
                a('Skink- Blue Tongue, Jabba', 'Carolyn M.', ['Target', 'Crate', 'Color Discrimination', 'Scale',
                                                               'Station'], [], ['Produce', 'Other']),
                a('Legless Lizard, Leggie', 'Audrey N.', ['Target'], [], ['Whole Prey', 'Inverts', 'Other']),
                a('Tortoise- Burmese Star, Aries', 'Audrey N.', ['Target', 'Color Discrimination', 'Station'],
                  ['Scale', 'Crate'], ['Produce', 'Other']),
                a('Tortoise- Burmese Star, Cassiopeia', 'Audrey N.', ['Target', 'Station', 'Color Discrimination'],
                  ['Scale', 'Crate', 'Dig'], ['Produce', 'Other']),
                a('Tortoise-Burmese Star, Corvus', 'Audrey N.',
                  ['Target', 'Station', 'Color Discrimination', 'Crate'], ['Scale'], ['Produce', 'Other']),
                a('Southern Toads, Dusk', 'Dakota H.', [], ['Station', 'Target', 'Handling'], ['Insects', 'Other']),
                a('Southern Toads, Thorn', 'Dakota H.', [], ['Station', 'Target', 'Handling'], ['Insects', 'Other']),
                a('Southern Toads, Willow', 'Dakota H.', [], ['Station', 'Target', 'Handling'], ['Insects', 'Other']),
                a('Dragon- Bearded, Joanna', 'Carolyn M.', ['Target', 'Crate', 'Station', 'Bonding'], [],
                  ['Insects', 'Produce', 'Other']),
                a('Frog- Whites, Toby', 'Audrey N.', [], ['Handling'], ['Insects', 'Other']),
            ],
        },
        {
            'name': 'Ambassador Mammal/ Bird',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Armadillo-Hairy, Rizzo', 'Kelsey H.',
                  ['Crate', 'Touch', 'Target', 'Recall', 'Up', 'Scale', 'Call to Session'],
                  ['Scent Discrimination'], ['Produce', 'Insects', 'Diet', 'Other']),
                a('Armadillo- Hairy, Malcolm', 'Audrey N.', ['Target', 'Crate', 'Up', 'Touch', 'Station'],
                  ['Nails'], ['Produce', 'Insects', 'Diet', 'Other']),
                a('Armadillo-Hairy, Alice', 'Kelsey H.',
                  ['Crate', 'Target', 'Up', 'Dig', 'Scent Discrimination', 'Scale', 'Call to Session'], [],
                  ['Produce', 'Insects', 'Diet', 'Other']),
                a('Chinchilla, Porg', 'Kelsey H.',
                  ['Station', 'Scale', 'Touch', 'Up', 'Ball', 'Target', 'Crate', 'Handling', 'Presentation',
                   'Tap Target'], ['Hold', 'In Hand'], ['Cereal', 'Oats', 'Dried Fruit', 'Produce', 'Other']),
                a('Chinchilla, Squirtle', 'Kelsey H.',
                  ['Station', 'Scale', 'Touch', 'Up', 'Ball', 'Target', 'Crate', 'Handling', 'Presentation',
                   'Tap Target'], ['Hold'], ['Cereal', 'Oats', 'Dried Fruit', 'Produce', 'Other']),
                a('Ferret-Domestic, Harry', 'Dakota H.', ['Target', 'Crate', 'Tube'], ['Station'],
                  ['Ferretvite', 'Diet', 'Other']),
                a('Ferret-Domestic, Narcissa', 'Dakota H.', ['Target', 'Crate', 'Tube'], ['Station'],
                  ['Ferretvite', 'Diet', 'Other']),
                a('Ferret-Domestic, Enid', 'Dakota H.', ['Target', 'Crate', 'Tube', 'Station'], [],
                  ['Ferretvite', 'Diet', 'Other']),
                a('Ferret-Domestic, Marnie', 'Dakota H.', ['Target', 'Crate', 'Tube', 'Station'], [],
                  ['Ferretvite', 'Diet', 'Other']),
                a('Tenrec, Eleven', 'Quinton W.', ['Target', 'Station'], ['Scale', 'Crate'], ['Insects', 'Other']),
                a('Porcupine-Prehensile-tailed, Gwen', 'Quinton W.',
                  ['Scale', 'Target', 'Crate', 'Up', 'Down', 'Stretch', 'Presentation'],
                  ['Blood Draw', 'Hand Inject'], ['Nuts', 'Dried Fruit', 'Diet', 'Fig', 'Produce', 'Other']),
                a('Virginia Opossum, Womby', None, [], ['Target', 'Hold', 'Station', 'Crate'], []),
            ],
        },
        {
            'name': 'Birdhouse String',
            'keepers': TERRESTRIAL_KEEPERS,
            'asgs': [
                a('Hornbill-Trumpeter, Jazz', 'Darcie H.', ['Station', 'Scale', 'Here'],
                  ['Crate', 'Shift', 'Bonding'], ['Produce', 'Other']),
                a('Hornbill-Trumpeter, Ronnie', 'Darcie H.', ['Station', 'Scale', 'Here'],
                  ['Crate', 'Shift', 'Bonding'], ['Produce', 'Other']),
                a('Hornbill-Trumpeter, Fitzgerald', 'Darcie H.', ['Station', 'Scale', 'Here'],
                  ['Bonding', 'Crate', 'Shift'], ['Produce', 'Other']),
                a('Kookaburra-Laughing, Burt', 'Darcie H.', ['Shift', 'Station', 'Scale'],
                  ['Crate', 'Bonding'], ['Insects', 'Whole Prey', 'Other']),
                a('Owl-Barn, Asteria', 'Darcie H.', [], ['Scale'], ['Whole Prey', 'Other']),
                a('Macaw- Green winged, Ruby', 'Darcie H.',
                  ['Scale', 'Station', 'Touch', 'Wings', 'Spinn', 'Step Up', 'Feet', 'Vocal', 'Bonding', 'Walk',
                   'Crate', 'Arm Step Up'], ['Voluntary Nail Trim', 'Syringe'], ['Nuts', 'Produce', 'Other']),
                a('Boa- Emerald Tree, Sam', None, [], [], []),
                a('Boa- Rosy, Stripe', None, [], [], []),
                a('Cockroaches- Madagascar hissing, Group', None, [], [], []),
                a('Millipedes- African Giant', None, [], [], []),
                a('Python- Ball, Forrest Gump', None, [], [], []),
                a('Cottonmouth, Norman', None, [], [], []),
            ],
        },
    ],
    'Aquatic': [
        {
            'name': 'Aquarium Mammal',
            'keepers': AQUARIUM_MAMMAL_KEEPERS,
            'asgs': [
                a('Otter-Asian small-clawed, Theodor', None,
                  ['Target', 'Touch', 'Up', 'Scale up', 'Chute', 'Hold', 'Recall', 'Squeeze', 'Crate'],
                  ['Emergency Recall', 'Poke', 'Foot'],
                  ['Fish', 'Shrimp', 'Clam', 'Insects', 'Kibble', 'Diet', 'Other']),
                a('Otter-Asian small-clawed, Sotong', None, ['Target', 'Touch', 'Up'],
                  ['Scale up', 'Chute', 'Hold', 'Recall', 'Squeeze', 'Emergency Recall', 'Poke', 'Crate', 'Quiet'],
                  ['Fish', 'Shrimp', 'Clam', 'Insects', 'Kibble', 'Diet', 'Other']),
                a('Otter-Asian small-clawed, Adhi', None, [], ['Crate', 'Squeeze', 'Up', 'Touch', 'Target', 'Scale'],
                  ['Fish', 'Shrimp', 'Clam', 'Insects', 'Kibble', 'Diet', 'Other']),
                a('Otter-Asian small-clawed, Athena', None, [], [], []),
                a('Monkey-Titi, Dexter', None, ['Up', 'Scale', 'Target', 'Squeeze'],
                  ['Crate', 'Hold', 'Touch', 'Hand', 'Foot', 'Down'], ['Diet', 'Peanut', 'Insects', 'Other']),
                a('Monkey-Titi, Sawyer', None, ['Up', 'Scale', 'Target', 'Squeeze'],
                  ['Crate', 'Hold', 'Touch', 'Hand', 'Foot', 'Down'], ['Diet', 'Peanut', 'Insects', 'Other']),
                a('Sloth, Indie', None, ['Recall', 'Target', 'Ultrasound', 'Station', 'Foot', 'Crate', 'Touch'],
                  ['Injection'], ['Diet', 'Peanuts', 'Other']),
            ],
        },
        {
            'name': 'Aquarium Bird/ Reptile',
            'keepers': AQUARIUM_OTHER_KEEPERS,
            'asgs': [
                a('Penguin-African, Artemis', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Carl', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Deacon', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Derek', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Donna', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Dwight', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Godzilla', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Guinn', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Jim', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Kaapse', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Kuechly', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin- African, Liza', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin- African, Lailey', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Niffler', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Pat', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Pilchard', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Possession', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Raven', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Sinclair', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Thea', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Tux', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Vello', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin-African, Turk', None, ['Scale', 'Encounters', 'Feed Experience'],
                  ['Free Feed', 'Penguin Parade'], ['Diet', 'Other']),
                a('Penguin, Colony', None, ['Feed Experience'], ['Free Feed', 'Scale'], ['Diet', 'Other']),
                a('Turtle-Mata Mata, Joker', None, [], [], []),
                a('Turtle-Mata Mata, Quinn', None, [], [], []),
                a('Grand Cayman Blue Iguana, Yondu', None, [], ['Target'], ['Diet', 'Other']),
                a('Northern Cayman Lizard, Draco', None, ['Target'],
                  ['Follow', 'Crate', 'Scale', 'Station', 'Handling', 'Chute', 'Poke'], ['Diet', 'Other']),
                a('Terrapin- Diamondback, Rover', None, ['Target', 'Station'], ['Net'], ['Diet', 'Other']),
                a('Terrapin- Diamondback, Millie', None, ['Target', 'Station'], ['Net'], ['Diet', 'Other']),
                a('Turtle- Alligator Snapping, Bone Crusher', None, ['Target'], ['Scale', 'Chute'],
                  ['Diet', 'Other']),
            ],
        },
        {
            'name': 'Aquarium Fish',
            'keepers': AQUARIUM_OTHER_KEEPERS,
            'asgs': [
                a('Ray- White-blotched river, Hodor', None, [], ['Target', 'Net'], ['Diet', 'Other']),
                a('Ray- White-blotched river, Papaya', None, ['Target'], ['Net'], ['Diet', 'Other']),
                a('Ray- White-blotched river', None, [], ['Target', 'Net'], ['Diet', 'Other']),
                a('Ray- White-blotched river', None, [], ['Target', 'Net'], ['Diet', 'Other']),
                a('Shark, Sandbar, Magneto', None, ['Target'], ['Stretcher'], ['Diet', 'Squid', 'Other']),
                a('Shark, Sandbar, Lex Luthor', None, ['Target'], ['Stretcher'], ['Diet', 'Squid', 'Other']),
                a('Ray, Southern, Rogue', None, ['Target', 'AtoB', 'Circle', 'Blue Bin', 'Tactile', 'Horizontal Hold'],
                  ['Belly', 'Stretcher'], ['Diet', 'Other']),
                a('Ray, White-spotted Eagle, Silver Surfer', None,
                  ['Target', 'AtoB', 'Circle', 'Blue Bin', 'Tactile', 'Horizontal Hold', 'Follow'],
                  ['Belly', 'Stretcher'], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Cownose', None, ['Target'], [], ['Diet', 'Other']),
                a('Ray, Group', None, ['Target'], ['Net', 'Stretcher'], ['Diet', 'Other']),
                a('Eel- Green Moray, Bruce', None, ['Target'], [], ['Diet', 'Other']),
                a('Porcupinefish, Spotfin, Prickles', None, ['Target'], [], ['Diet', 'Other']),
                a('Octopus, Giant Pacific', None, ['Weigh Basket'], ['Touch'], ['Diet', 'Other']),
                a('Porcupinefish, Freckled, Mylar', None, ['Target'], ['Howdy'], ['Diet', 'Other']),
                a('Wolfeel, Peacock, Allie', None, ['Target', 'Weigh Basket', 'Tactile', 'AtoB'], [],
                  ['Diet', 'Other']),
                a('Epaulette Shark, Big', None, ['Pole Feed'], ['Station', 'Target'], ['Diet', 'Other']),
                a('Epaulette Shark, Small', None, ['Pole Feed'], ['Station', 'Target'], ['Diet', 'Other']),
                a('Whitespotted Bamboo Shark, Light', None, ['Pole Feed'], ['Station', 'Target'], ['Diet', 'Other']),
                a('Whitespotted Bamboo Shark, Dark', None, ['Pole Feed'], ['Station', 'Target'], ['Diet', 'Other']),
                a('Whitespotted Bamboo Shark, Super Dark', None, ['Pole Feed'], ['Station', 'Target'],
                  ['Diet', 'Other']),
                a('Brownbanded Bamboo Shark', None, ['Pole Feed'], ['Station', 'Target'], ['Diet', 'Other']),
                a('Red Drum, Rudy', None, ['Target'], ['Net'], ['Diet', 'Other']),
                a('Red Drum, 3 Spot', None, ['Target'], ['Net'], ['Diet', 'Other']),
                a('Red Drum, 4 Spot', None, ['Target'], ['Net'], ['Diet', 'Other']),
                a('Drum School', None, ['Target'], ['Net'], []),
                a('Peacock Mantis Shrimp', None, [], ['Target'], ['Diet', 'Other']),
            ],
        },
    ],
}


def username_for(token, division_name):
    token = token.strip()
    if token in SPLIT_NAMES:
        suffix = '1' if division_name == 'Terrestrial' else '2'
        return f'{token.lower()}{suffix}'
    return re.sub(r'[^a-z0-9]', '', token.lower())


class Command(BaseCommand):
    help = 'Preload Divisions/Strings/TrainingAnimals/Behaviors/Reinforcers/keepers from Animal Behavior Master List.pdf'

    @transaction.atomic
    def handle(self, *args, **options):
        name_counts = {}
        users_created = 0
        users_existing = 0
        asgs_created = 0
        asgs_existing = 0
        skipped = []

        for division_name, strings in DIVISIONS.items():
            division, _ = Division.objects.get_or_create(name=division_name)

            for string_data in strings:
                string_obj, _ = String.objects.get_or_create(name=string_data['name'], defaults={'division': division})
                if string_obj.division_id != division.id:
                    string_obj.division = division
                    string_obj.save()

                keeper_users = []
                for token in string_data['keepers']:
                    token = token.strip()
                    if token.lower() == 'other':
                        continue
                    username = username_for(token, division_name)
                    user, created = User.objects.get_or_create(username=username)
                    if created:
                        user.set_password(PASSWORD)
                        user.save()
                        users_created += 1
                    else:
                        users_existing += 1
                    keeper_users.append(user)
                string_obj.keepers.add(*keeper_users)

                for asg_data in string_data['asgs']:
                    raw_name = asg_data['name']
                    if raw_name in SKIPPED_ASGS:
                        skipped.append(raw_name)
                        continue

                    count = name_counts.get(raw_name, 0) + 1
                    name_counts[raw_name] = count
                    final_name = raw_name if count == 1 else f'{raw_name} ({count})'

                    notes = f"Primary Trainer: {asg_data['trainer']}" if asg_data['trainer'] else ''
                    asg_obj, created = TrainingAnimal.objects.get_or_create(
                        name=final_name, defaults={'string': string_obj, 'notes': notes},
                    )
                    if created:
                        asgs_created += 1
                    else:
                        asgs_existing += 1
                        if asg_obj.string_id != string_obj.id:
                            self.stdout.write(self.style.WARNING(
                                f'"{final_name}" already exists under a different string; leaving it as-is.'
                            ))

                    for behavior_name in asg_data['maint']:
                        behavior, _ = Behavior.objects.get_or_create(name=behavior_name, behavior_type='maintenance')
                        asg_obj.maintenance_behaviors.add(behavior)
                    for behavior_name in asg_data['new']:
                        behavior, _ = Behavior.objects.get_or_create(name=behavior_name, behavior_type='new')
                        asg_obj.new_behaviors.add(behavior)
                    for reinforcer_name in asg_data['reinf']:
                        reinforcer, _ = Reinforcer.objects.get_or_create(name=reinforcer_name)
                        asg_obj.reinforcers.add(reinforcer)

        self.stdout.write(self.style.SUCCESS(
            f'Users: {users_created} created, {users_existing} already existed (password "{PASSWORD}" set on new ones).'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Training animals: {asgs_created} created, {asgs_existing} already existed.'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(f'Skipped (struck through in source): {", ".join(skipped)}'))
