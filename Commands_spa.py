import json
import logging as log
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import MainController
import GamesController
from Constants.Config import STATS
from Boardgamebox.Board import Board
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Constants.Config import ADMIN

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

commands = [  # command description used in the "help" command
    '/help - Proporciona información sobre los comandos disponibles',
    '/start - Presenta un pequeño resumen sobre Secret Hitler',
    '/symbols - Muestra los posibles símbolos y su significado',
    '/rules - Link a las reglas oficiales de Secret Hitler',
    '/newgame - Crea un nuevo juego',
    '/join - Te incorpora a un juego existente',
    '/startgame - Comienza un juego ya creado',
    '/cancelgame - Cancela un juego existente. Se perderá toda la información de la partida',
    '/board - Muestra el tablero actual, con los marcadores de Fascistas y Liberales, orden presidencial y contador de elecciones',
    '/history - Muestra el historial del juego actual',
    '/votes - Muestra quién votó en la elección actual'
]

symbols = [
    u"\u25FB\uFE0F" + ' Espacio vacío  que no brinda ningún poder',
    u"\u2716\uFE0F" + ' Espacio cubierto por una carta',  # X
    u"\U0001F52E" + ' Poder Presidencial: Vistazo a las políticas',  # crystal
    u"\U0001F50E" + ' Poder Presidencial: Investigar Lealtad',  # inspection glass
    u"\U0001F5E1" + ' Poder Presidencial: Ejecución',  # knife
    u"\U0001F454" + ' Poder Presidencial: Llamado a elecciones extraordinarias',  # tie
    u"\U0001F54A" + ' Victoria Liberal',  # dove
    u"\u2620" + ' Victoria Fascista'  # skull
]


def command_symbols(bot, update):
    cid = update.message.chat_id
    symbol_text = "Los siguientes símbolos pueden aparecer en el tablero: \n"
    for i in symbols:
        symbol_text += i + "\n"
    bot.send_message(cid, symbol_text)


def command_board(bot, update):
    cid = update.message.chat_id
    if cid in GamesController.games.keys():
        if GamesController.games[cid].board:
            bot.send_message(cid, GamesController.games[cid].board.print_board())
        else:
            bot.send_message(cid, "No hay juego en curso en este grupo. Por favor, iniciarlo utilizando /startgame")
    else:
        bot.send_message(cid, "No se ha creado un juego. Crearlo utilizando /newgame")


def command_start(bot, update):
    cid = update.message.chat_id
    bot.send_message(cid,
                     "\"Secret Hitler es un juego de deducción social para 5-10 personas sobre encontrar y detener al Secret Hitler."
                     " La mayoría de los jugadores son liberales. Si logran confiar entre sí, tendrán suficientes "
                     "votos para controlar la partida y ganar el juego. Pero algunos son fascistas. Ellos dirán lo que sea "
                     "necesario para ser elegidos, llevar a cabo sus planes, y culpar a otros por la caída. Los liberales deben "
                     "trabajar juntos para descubrir la verdad antes de que los fascistas proclamen a su frío líder y ganen el juego."
                     ".\"\n- Descripción oficial de Secret Hitler\n\nAgrégame a un grupo y escribe /newgame para crear una partida.")
    command_help(bot, update)


def command_rules(bot, update):
    cid = update.message.chat_id
    btn = [[InlineKeyboardButton("Rules", url="http://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")]]
    rulesMarkup = InlineKeyboardMarkup(btn)
    bot.send_message(cid, "Lee las reglas oficiales de Secret Hitler:", reply_markup=rulesMarkup)


# pings the bot
def command_ping(bot, update):
    cid = update.message.chat_id
    bot.send_message(cid, 'pong - v0.3')


# prints statistics, only ADMIN
def command_stats(bot, update):
    cid = update.message.chat_id
    if cid == ADMIN:
        with open(STATS, 'r') as f:
            stats = json.load(f)
        stattext = "+++ Statistics +++\n" + \
                    "Liberal Wins (policies): " + str(stats.get("libwin_policies")) + "\n" + \
                    "Liberal Wins (killed Hitler): " + str(stats.get("libwin_kill")) + "\n" + \
                    "Fascist Wins (policies): " + str(stats.get("fascwin_policies")) + "\n" + \
                    "Fascist Wins (Hitler chancellor): " + str(stats.get("fascwin_hitler")) + "\n" + \
                    "Games cancelled: " + str(stats.get("cancelled")) + "\n\n" + \
                    "Total amount of groups: " + str(len(stats.get("groups"))) + "\n" + \
                    "Games running right now: "
        bot.send_message(cid, stattext)       


# help page
def command_help(bot, update):
    cid = update.message.chat_id
    help_text = "Los siguientes comandos están disponibles:\n"
    for i in commands:
        help_text += i + "\n"
    bot.send_message(cid, help_text)


def command_newgame(bot, update):  
    cid = update.message.chat_id
    try:
      game = GamesController.games.get(cid, None)
      groupType = update.message.chat.type
      if groupType not in ['group', 'supergroup']:
          bot.send_message(cid, "Debes agregarme a un grupo primero y escribir /newgame allí.")
      elif game:
          bot.send_message(cid, "Ya hay un juego en curso. Si quieres finalizarlo escribe /cancelgame.")
      else:
          GamesController.games[cid] = Game(cid, update.message.from_user.id)
          '''
          with open(STATS, 'r') as f:
              stats = json.load(f)
          if cid not in stats.get("groups"):
              stats.get("groups").append(cid)
              with open(STATS, 'w') as f:
                  json.dump(stats, f)
          '''
          bot.send_message(cid, "Un nuevo juego ha sido creado. Cada jugador debe unirse escribiendo /join.\nQuien inició el juego (o el administrador del grupo) puede unirse también y enviar /startgame cuando todos se hayan unido al juego.")
    except Exception as e:
      bot.send_message(cid, str(e))


def command_join(bot, update):
    groupName = update.message.chat.title
    cid = update.message.chat_id
    groupType = update.message.chat.type
    game = GamesController.games.get(cid, None)
    fname = update.message.from_user.first_name

    if groupType not in ['group', 'supergroup']:
        bot.send_message(cid, "Debes agregarme a un grupo primero y escribir /newgame allí.")
    elif not game:
        bot.send_message(cid, "No se ha creado un juego. Crearlo utilizando /newgame")
    elif game.board:
        bot.send_message(cid, "El juego ya ha comenzado. Por favor espera al próximo.")
    elif update.message.from_user.id in game.playerlist:
        bot.send_message(game.cid, "Ya te uniste al juego, %s." % fname)
    elif len(game.playerlist) >= 10:
        bot.send_message(game.cid, "Han alcanzado el máximo de jugadores. Inicia el juego mediante /startgame.")
    else:
        uid = update.message.from_user.id
        player = Player(fname, uid)
        try:
            bot.send_message(uid, "Te uniste a un juego en %s. Pronto te diré tu rol secreto." % groupName)
            game.add_player(uid, player)
        except Exception:
            bot.send_message(game.cid,
                             fname + ", No puedo enviarte un mensaje privado. Por favor ve a @thesecrethitlerbot y haz click en \"Start\".\nLuego debes enviar /join nuevamente para unirte .")
        log.info("%s (%d) se unió a un juego en %d" % (fname, uid, game.cid))
        if len(game.playerlist) > 4:
            bot.send_message(game.cid, fname + " se ha unido al juego. Envía /startgame si fue el último jugador y quieres empezaron con %d participantes." % len(game.playerlist))
        elif len(game.playerlist) == 1:
            bot.send_message(game.cid, "%s se ha unido al juego. Actualmente hay %d jugadores en la partida y son necesarios entre 5 y 10." % (fname, len(game.playerlist)))
        else:
            bot.send_message(game.cid, "%s se ha unido al juego. Actualmente hay %d jugadores en la partida y son necesarios entre 5 y 10." % (fname, len(game.playerlist)))


def command_startgame(bot, update):
    log.info('command_startgame called')
    cid = update.message.chat_id
    game = GamesController.games.get(cid, None)
    if not game:
        bot.send_message(cid, "No hay juego en curso en este grupo. Por favor, iniciarlo utilizando /startgame")
    elif game.board:
        bot.send_message(cid, "El juego ya está en marcha.")
    elif update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
        bot.send_message(game.cid, "Sólo quien creó el juego o un administrador del grupo puede iniciar la partida /startgame.")
    elif len(game.playerlist) < 5:
        bot.send_message(game.cid, "No hay jugadores suficientes (mín. 5, máx. 10). Únete al juego mediante /join.")
    else:
        player_number = len(game.playerlist)
        MainController.inform_players(bot, game, game.cid, player_number)
        MainController.inform_fascists(bot, game, player_number)
        game.board = Board(player_number, game)
        log.info(game.board)
        log.info("len(games) Command_startgame: " + str(len(GamesController.games)))
        game.shuffle_player_sequence()
        game.board.state.player_counter = 0
        bot.send_message(game.cid, game.board.print_board())
        #group_name = update.message.chat.title
        #bot.send_message(ADMIN, "Game of Secret Hitler started in group %s (%d)" % (group_name, cid))
        MainController.start_round(bot, game)

def command_cancelgame(bot, update):
    log.info('command_cancelgame called')
    cid = update.message.chat_id
    if cid in GamesController.games.keys():
        game = GamesController.games[cid]
        status = bot.getChatMember(cid, update.message.from_user.id).status
        if update.message.from_user.id == game.initiator or status in ("administrator", "creator"):
            MainController.end_game(bot, game, 99)
        else:
            bot.send_message(cid, "Sólo quien creó el juego o un administrador del grupo puede cancelar la partida utilizando /cancelgame")
    else:
        bot.send_message(cid, "No se ha creado un juego. Crearlo utilizando /newgame")

def command_votes(bot, update):
    try:
      #Send message of executing command   
      cid = update.message.chat_id
      bot.send_message(cid, "Buscando el historial...")
      #Check if there is a current game 
      if cid in GamesController.games.keys():
        game = GamesController.games.get(cid, None)
        if not game.dateinitvote:
          # If date of init vote is null, then the voting didnt start          
          bot.send_message(cid, "La votación aún no comenzó.")
        else:
          #If there is a time, compare it and send history of votes.
          start = game.dateinitvote
          stop = datetime.datetime.now()          
          elapsed = stop - start
          if elapsed > datetime.timedelta(minutes=1):
            history_text = "Votación para el Presidente %s y el Canciller %s:\n" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name) 
            for i in game.history[game.currentround]:
                history_text += i + "\n"
            bot.send_message(cid, history_text)
          else:
            bot.send_message(cid, "Deben pasar 5 minutos para ver los votos") 
      else:
        bot.send_message(cid, "No se ha creado un juego. Crearlo utilizando /newgame")
    except Exception as e:
      bot.send_message(cid, str(e))
        
def command_showhistory(bot, update):
    #game.pedrote = 3
    try:
      #Send message of executing command   
      cid = update.message.chat_id
      
      #bot.send_message(cid, "Looking for history...")
      bot.send_message(cid, "Debug info")
      bot.send_message(cid, "Current chat id: " + str(cid))
      #Check if there is a current game 
      if cid in GamesController.games.keys():
        game = GamesController.games.get(cid, None)    

        
        bot.send_message(cid, "Current round: " + str(game.currentround))
        
        history_text = "Historial del partido actual:\n"
        for x in range(0, game.currentround):
          for i in game.history[x]:
            history_text += i + "\n"
        bot.send_message(cid, history_text)
        #for i in game.history[game.currentround]:
        #        history_text += i + "\n"
        #Simulating start of voting
        #game.currentround
        '''
        if game.currentround == 0:
          # I create a new list for each game round
          game.history.append([])
          # Change game round so it starts adding votes in this simulation
          game.currentround = 1
        else:
          # If voting round started. update.message.from_user.id
          game.history[0].append("Pepe voto %s" % (game.currentround))
          game.currentround += 1
          
        if game.currentround == 5:
          history_text = "Historial para el partido actual:\n"
          for i in game.history[0]:
              history_text += i + "\n"
          bot.send_message(cid, history_text)
        '''
        
        
        
        
        '''
        # Time managment to handle the voting command
        if not game.dateinitvote:
          # If date of init vote is null, assign it.
          game.dateinitvote = datetime.datetime.now()
          bot.send_message(cid, "Se ha comenzado a contar.")
        else:
          #If there is a time, compare it and send minutes.
          start = game.dateinitvote
          stop = datetime.datetime.now()          
          elapsed = stop - start
          if elapsed > datetime.timedelta(minutes=2):
            bot.send_message(cid, "Han pasado mas de 2 minutos")
        '''   
        
        
      else:
        bot.send_message(cid, "No se ha creado un juego. Crearlo utilizando /newgame")
    except Exception as e:
      bot.send_message(cid, str(e))
      log.error("Unknown error: " + str(e))
        
        
