from flask import Blueprint, request, jsonify
import random
from typing import List, Optional, Tuple

# Constants
DIMENSIONS = 3
DRAW = 0
PLAYER_X = 1
PLAYER_O = 2
SCORES = {
    PLAYER_X: 1,
    DRAW: 0,
    PLAYER_O: -1
}

GAME_MODES = {
    'easy': 'easy',
    'medium': 'medium',
    'difficult': 'difficult'
}

# Create blueprint
tic_tac_toe_bp = Blueprint('tic_tac_toe', __name__)

class Board:
    def __init__(self, grid: Optional[List[Optional[int]]] = None):
        self.grid = grid if grid is not None else [None] * (DIMENSIONS ** 2)
        self.winning_index = None
    
    def make_move(self, square: int, player: int) -> None:
        """Make a move on the board if the square is empty."""
        if self.grid[square] is None:
            self.grid[square] = player
    
    def get_empty_squares(self, grid: Optional[List[Optional[int]]] = None) -> List[int]:
        """Get indices of all empty squares."""
        if grid is None:
            grid = self.grid
        return [i for i, square in enumerate(grid) if square is None]
    
    def is_empty(self, grid: Optional[List[Optional[int]]] = None) -> bool:
        """Check if the board is completely empty."""
        if grid is None:
            grid = self.grid
        return len(self.get_empty_squares(grid)) == DIMENSIONS ** 2
    
    def get_winner(self, grid: Optional[List[Optional[int]]] = None) -> Optional[int]:
        """Check for a winner and return the winning player or DRAW."""
        if grid is None:
            grid = self.grid
            
        winning_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        
        for i, combo in enumerate(winning_combos):
            if (grid[combo[0]] is not None and 
                grid[combo[0]] == grid[combo[1]] == grid[combo[2]]):
                self.winning_index = i
                return grid[combo[0]]
        
        # Check for draw
        if len(self.get_empty_squares(grid)) == 0:
            self.winning_index = None
            return DRAW
            
        return None
    
    def clone(self) -> 'Board':
        """Create a copy of the current board."""
        return Board(self.grid.copy())

def switch_player(player: int) -> int:
    """Switch between PLAYER_X and PLAYER_O."""
    return PLAYER_O if player == PLAYER_X else PLAYER_X

def minimax(board: Board, player: int) -> Tuple[int, Optional[int]]:
    """
    Minimax algorithm implementation.
    Returns a tuple of (score, best_move).
    """
    multiplier = SCORES[player]
    max_score = -1
    best_move = None
    
    winner = board.get_winner()
    if winner is not None:
        return SCORES[winner], None
    
    for square in board.get_empty_squares():
        board_copy = board.clone()
        board_copy.make_move(square, player)
        score = multiplier * minimax(board_copy, switch_player(player))[0]
        
        if score >= max_score:
            max_score = score
            best_move = square
    
    return multiplier * max_score, best_move

@tic_tac_toe_bp.route('/ai/move', methods=['POST'])
def ai_move():
    """
    Endpoint to get AI move.
    
    Expected JSON payload:
    {
        "grid": [null, 1, null, 2, null, null, null, null, null],
        "ai_player": 2,
        "mode": "difficult"
    }
    
    Returns:
    {
        "success": true,
        "move_index": 4,
        "grid": [null, 1, null, 2, 2, null, null, null, null]
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        grid = data.get('grid')
        ai_player = data.get('ai_player')
        mode = data.get('mode', 'difficult')
        
        # Validate input
        if grid is None or ai_player is None:
            return jsonify({'success': False, 'message': 'Missing required fields: grid, ai_player'}), 400
        
        if len(grid) != 9:
            return jsonify({'success': False, 'message': 'Grid must have exactly 9 elements'}), 400
        
        if ai_player not in [PLAYER_X, PLAYER_O]:
            return jsonify({'success': False, 'message': 'ai_player must be 1 (X) or 2 (O)'}), 400
        
        if mode not in GAME_MODES.values():
            return jsonify({'success': False, 'message': 'Invalid mode. Use: easy, medium, or difficult'}), 400
        
        # Create board and get empty squares
        board = Board(grid.copy())
        empty_squares = board.get_empty_squares()
        
        if not empty_squares:
            return jsonify({'success': False, 'message': 'No valid moves available'}), 400
        
        move_index = None
        
        # AI Logic based on mode
        if mode == GAME_MODES['easy']:
            # Easy mode: Random moves
            move_index = random.choice(empty_squares)
            
        elif mode == GAME_MODES['medium']:
            # Medium mode: 50% smart moves, 50% random moves
            if board.is_empty() or random.random() < 0.5:
                move_index = random.choice(empty_squares)
            else:
                _, move_index = minimax(board, ai_player)
                
        else:  # difficult mode
            # Difficult mode: Always use minimax, except for first move (random for efficiency)
            if board.is_empty():
                move_index = random.randint(0, 8)
            else:
                _, move_index = minimax(board, ai_player)
        
        # Make the move
        if move_index is not None and move_index in empty_squares:
            new_grid = grid.copy()
            new_grid[move_index] = ai_player
            
            return jsonify({
                'success': True,
                'move_index': move_index,
                'grid': new_grid,
                'ai_player': ai_player
            })
        else:
            return jsonify({'success': False, 'message': 'Unable to determine valid move'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@tic_tac_toe_bp.route('/game/check_winner', methods=['POST'])
def check_winner():
    """
    Endpoint to check for game winner.
    
    Expected JSON payload:
    {
        "grid": [1, 1, 1, 2, 2, null, null, null, null]
    }
    
    Returns:
    {
        "winner": 1,
        "game_over": true,
        "winner_name": "Player X",
        "winning_index": 0
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        grid = data.get('grid')
        
        if grid is None:
            return jsonify({'success': False, 'message': 'Missing required field: grid'}), 400
        
        if len(grid) != 9:
            return jsonify({'success': False, 'message': 'Grid must have exactly 9 elements'}), 400
        
        board = Board(grid)
        winner = board.get_winner()
        
        result = {
            'winner': winner,
            'game_over': winner is not None,
            'winning_index': board.winning_index
        }
        
        if winner == PLAYER_X:
            result['winner_name'] = 'Player X'
        elif winner == PLAYER_O:
            result['winner_name'] = 'Player O'
        elif winner == DRAW:
            result['winner_name'] = 'Draw'
        else:
            result['winner_name'] = None
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@tic_tac_toe_bp.route('/game/reset', methods=['POST'])
def reset_game():
    """
    Endpoint to get a fresh game state.
    
    Returns:
    {
        "success": true,
        "grid": [null, null, null, null, null, null, null, null, null],
        "message": "Game reset successfully"
    }
    """
    try:
        fresh_grid = [None] * 9
        return jsonify({
            'success': True,
            'grid': fresh_grid,
            'message': 'Game reset successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500