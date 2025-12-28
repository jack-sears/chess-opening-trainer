// Chess Opening Trainer - Frontend JavaScript

console.log('app.js script loaded');

let sessionId = null;
let currentGame = null;
let board = null;
let currentPosition = null;
let hintSquare = null;
let pendingMove = null; // Track move being submitted to avoid double updates

// Helper to get Chess class - handles different loading scenarios
function getChessClass() {
    // Try different possible exports from chess.js
    // chess.js 0.13.4 exports Chess as a global variable
    if (typeof Chess !== 'undefined') {
        return Chess;
    }
    if (typeof window !== 'undefined' && typeof window.Chess !== 'undefined') {
        return window.Chess;
    }
    // Some versions might export differently
    if (typeof Chessjs !== 'undefined' && Chessjs.Chess) {
        return Chessjs.Chess;
    }
    if (typeof window !== 'undefined' && typeof window.Chessjs !== 'undefined' && window.Chessjs.Chess) {
        return window.Chessjs.Chess;
    }
    // Check if it's available but with different case
    if (typeof window !== 'undefined') {
        const chessKeys = Object.keys(window).filter(k => k.toLowerCase().includes('chess'));
        if (chessKeys.length > 0) {
            console.warn('Chess class not found. Available chess-related globals:', chessKeys);
        }
    }
    return null;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    try {
        // Initialize setup screen immediately - we don't need Chess.js until training starts
        initializeSetup();
        loadPGNFiles();
    } catch (error) {
        console.error('Error during initialization:', error);
        console.error('Error stack:', error.stack);
        // Show error on page
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; background: red; color: white; padding: 20px; z-index: 10000;';
        errorDiv.textContent = 'Error initializing app: ' + error.message + '. Check console for details.';
        document.body.appendChild(errorDiv);
    }
});

// Setup Screen Functions
function initializeSetup() {
    try {
        const startBtn = document.getElementById('start-training-btn');
        const backBtn = document.getElementById('back-to-setup-btn');
        
        if (!startBtn) {
            throw new Error('start-training-btn element not found');
        }
        if (!backBtn) {
            throw new Error('back-to-setup-btn element not found');
        }
        
        startBtn.addEventListener('click', startTraining);
        backBtn.addEventListener('click', () => {
            const setupScreen = document.getElementById('setup-screen');
            const trainingScreen = document.getElementById('training-screen');
            if (setupScreen) setupScreen.classList.add('active');
            if (trainingScreen) trainingScreen.classList.remove('active');
        });
        
        console.log('Setup initialized successfully');
    } catch (error) {
        console.error('Error in initializeSetup:', error);
        throw error;
    }
}

async function loadPGNFiles() {
    try {
        const response = await fetch('/api/pgn/list');
        const data = await response.json();
        
        const whiteContainer = document.getElementById('white-openings');
        const blackContainer = document.getElementById('black-openings');
        
        whiteContainer.innerHTML = '';
        blackContainer.innerHTML = '';
        
        data.white.forEach(file => {
            const checkbox = createCheckbox(file, 'white');
            whiteContainer.appendChild(checkbox);
        });
        
        data.black.forEach(file => {
            const checkbox = createCheckbox(file, 'black');
            blackContainer.appendChild(checkbox);
        });
    } catch (error) {
        console.error('Error loading PGN files:', error);
        showError('Failed to load PGN files');
    }
}

function createCheckbox(filename, color) {
    const div = document.createElement('div');
    div.className = 'checkbox-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `pgn-${color}-${filename}`;
    checkbox.value = filename;
    
    const label = document.createElement('label');
    label.htmlFor = checkbox.id;
    label.textContent = filename.replace('.pgn', '');
    
    div.appendChild(checkbox);
    div.appendChild(label);
    
    return div;
}

async function startTraining() {
    const username = document.getElementById('username').value || 'guest';
    const selectedFiles = getSelectedFiles();
    
    if (selectedFiles.length === 0) {
        showError('Please select at least one opening to practice');
        return;
    }
    
    try {
        const response = await fetch('/api/training/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                selectedFiles: selectedFiles
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start training');
        }
        
        const data = await response.json();
        sessionId = data.sessionId;
        
        // Switch to training screen
        document.getElementById('setup-screen').classList.remove('active');
        document.getElementById('training-screen').classList.add('active');
        
        document.getElementById('display-username').textContent = username;
        
        // Wait a moment for screen transition, then initialize board
        setTimeout(() => {
            // Initialize chess board
            initializeChessBoard();
            
            // Load first line after board is ready
            setTimeout(() => {
                loadNextLine();
            }, 500);
        }, 100);
        
    } catch (error) {
        console.error('Error starting training:', error);
        showError(error.message);
    }
}

function getSelectedFiles() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Chess Board Functions
function initializeChessBoard() {
    console.log('=== Initializing chess board ===');
    
    // Wait for ChessBoard to be available
    let attempts = 0;
    const maxAttempts = 50; // 5 seconds max wait
    
    const initBoard = () => {
        attempts++;
        console.log('Init attempt:', attempts);
        
        // Check if ChessBoard is available
        // Check for ChessBoard - it might be window.ChessBoard or just ChessBoard
        const ChessBoardLib = typeof ChessBoard !== 'undefined' ? ChessBoard : 
                              (typeof window !== 'undefined' && typeof window.ChessBoard !== 'undefined' ? window.ChessBoard : null);
        
        if (!ChessBoardLib) {
            if (attempts >= maxAttempts) {
                console.error('ChessBoard library failed to load after', maxAttempts * 100, 'ms');
                console.error('Available window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('chess')));
                console.error('jQuery available:', typeof jQuery !== 'undefined');
                showError('ChessBoard library failed to load. Check console for details.');
                return;
            }
            console.log('Waiting for ChessBoard library... attempt', attempts);
            setTimeout(initBoard, 100);
            return;
        }
        
        // Store reference to ChessBoard
        window.ChessBoard = ChessBoardLib;
        
        console.log('✓ ChessBoard library loaded');
        
        // Check for container
        const container = document.getElementById('board-container');
        if (!container) {
            console.error('✗ board-container element not found!');
            showError('Board container not found. Please refresh the page.');
            return;
        }
        console.log('✓ Board container found');
        
        // Clear and create board div
        container.innerHTML = '';
        const boardDiv = document.createElement('div');
        boardDiv.id = 'chessboard';
        boardDiv.style.width = '400px';
        boardDiv.style.margin = '0 auto';
        container.appendChild(boardDiv);
        
        console.log('✓ Board div created');
        
        // Wait a tiny bit for DOM to update
        setTimeout(() => {
            const chessboardDiv = document.getElementById('chessboard');
            if (!chessboardDiv) {
                console.error('✗ chessboard div not found after creation!');
                showError('Failed to create board element.');
                return;
            }
            
            console.log('✓ Chessboard div verified in DOM');
            
            const config = {
                position: 'start',
                draggable: true,
                onDragStart: onDragStart,
                onDrop: onDrop,
                onSnapEnd: onSnapEnd,
                pieceTheme: (piece) => {
                    // Map chessboard.js piece notation to image filenames
                    // White pieces have 'w' prefix (wK, wQ, etc.)
                    // Black pieces don't have prefix (K, Q, etc.)
                    const pieceMap = {
                        'wK': 'wK', 'wQ': 'wQ', 'wR': 'wR', 'wB': 'wB', 'wN': 'wN', 'wP': 'wP',
                        'bK': 'K', 'bQ': 'Q', 'bR': 'R', 'bB': 'B', 'bN': 'N', 'bP': 'P'
                    };
                    const filename = pieceMap[piece] || piece;
                    const imagePath = `/static/pieces/${filename}.png`;
                    return imagePath;
                },
                orientation: 'white'
            };
            
            try {
                console.log('Attempting ChessBoard initialization...');
                const ChessBoardLib = typeof ChessBoard !== 'undefined' ? ChessBoard : 
                                      (typeof window !== 'undefined' && typeof window.ChessBoard !== 'undefined' ? window.ChessBoard : null);
                console.log('ChessBoard type:', typeof ChessBoardLib);
                console.log('Chessboard element:', chessboardDiv);
                console.log('Element parent:', chessboardDiv.parentElement);
                
                if (!ChessBoardLib) {
                    throw new Error('ChessBoard function not available');
                }
                
                board = ChessBoardLib('chessboard', config);
                
                if (!board) {
                    console.error('✗ ChessBoard returned null/undefined');
                    showError('Failed to initialize chess board.');
                    return;
                }
                
                console.log('✓ ChessBoard initialized successfully');
                console.log('Board object:', board);
                
                // Check if board actually rendered
                setTimeout(() => {
                    const boardElement = document.getElementById('chessboard');
                    if (boardElement) {
                        const computedStyle = window.getComputedStyle(boardElement);
                        console.log('Board element styles:', {
                            display: computedStyle.display,
                            width: computedStyle.width,
                            height: computedStyle.height,
                            visibility: computedStyle.visibility,
                            offsetWidth: boardElement.offsetWidth,
                            offsetHeight: boardElement.offsetHeight
                        });
                        
                        // Check for chessboard squares
                        const squares = boardElement.querySelectorAll('.square-55d63');
                        console.log('Number of squares found:', squares.length);
                        
                        if (squares.length === 0) {
                            console.error('✗ No chessboard squares found - board may not have rendered');
                            showError('Chess board failed to render. Check console for details.');
                        } else {
                            console.log('✓ Chessboard squares found - board rendered successfully');
                        }
                    }
                }, 200);
                
            } catch (error) {
                console.error('✗ Error initializing ChessBoard:', error);
                console.error('Error name:', error.name);
                console.error('Error message:', error.message);
                console.error('Error stack:', error.stack);
                showError('Failed to initialize chess board: ' + error.message);
            }
        }, 10);
        
        // Initialize buttons
        try {
            const hintBtn = document.getElementById('hint-btn');
            const solutionBtn = document.getElementById('solution-btn');
            const nextLineBtn = document.getElementById('next-line-btn');
            
            if (hintBtn) hintBtn.addEventListener('click', showHint);
            if (solutionBtn) solutionBtn.addEventListener('click', showSolution);
            if (nextLineBtn) nextLineBtn.addEventListener('click', loadNextLine);
            console.log('✓ Board buttons initialized');
        } catch (error) {
            console.error('Error initializing buttons:', error);
        }
    };
    
    initBoard();
}

function onDragStart(source, piece, position, orientation) {
    console.log('onDragStart called:', source, piece);
    console.log('Current position:', currentPosition);
    
    // Allow dragging if no position info yet (initial state - board just loaded)
    if (!currentPosition) {
        console.log('No position info yet, allowing drag');
        return true;
    }
    
    // If position info says it's not user's turn, but we don't have a game loaded yet, allow it
    if (currentPosition.isUserTurn === false && !currentGame) {
        console.log('Position says not user turn but no game loaded, allowing drag');
        return true;
    }
    
    // Only allow dragging if it's the user's turn
    if (currentPosition.isUserTurn === false) {
        console.log('Not user turn, blocking drag');
        return false;
    }
    
    // Only allow dragging user's pieces
    const pieceColor = piece[0] === 'w' ? 'white' : 'black';
    const userColor = currentPosition.userColor || 'white'; // default to white
    
    if (pieceColor !== userColor) {
        console.log('Piece color mismatch, blocking drag:', pieceColor, 'vs', userColor);
        return false;
    }
    
    console.log('Drag allowed');
    return true;
}

function onDrop(source, target) {
    console.log('onDrop called:', source, 'to', target);
    console.log('Current position:', currentPosition);
    
    // If no position info yet, allow the move and let the server validate
    if (!currentPosition) {
        console.log('No position info, allowing move to be submitted');
        const move = source + target;
        pendingMove = move;
        submitMove(move);
        return 'snapback'; // Will update after server response
    }
    
    // Block if explicitly not user's turn (but allow if undefined/null)
    if (currentPosition.isUserTurn === false) {
        console.log('Drop blocked: not user turn');
        return 'snapback';
    }
    
    const move = source + target;
    console.log('Move attempted:', move);
    pendingMove = move; // Track this move
    
    // Check for promotion if we have the game object
    let promotionMove = null;
    if (currentGame) {
        try {
            const piece = currentGame.get(source);
            if (piece && piece.type === 'p') {
                const rank = target[1];
                if ((piece.color === 'w' && rank === '8') || (piece.color === 'b' && rank === '1')) {
                    // For now, default to queen promotion
                    // Could add a promotion dialog later
                    console.log('Pawn promotion detected');
                    promotionMove = move + 'q';
                }
            }
        } catch (error) {
            console.error('Error checking promotion:', error);
        }
    }
    
    // Store the board state before move in case we need to revert
    const boardFenBeforeMove = currentGame ? currentGame.fen() : null;
    
    // Don't pre-update the board - let the piece stay where dropped visually
    // We'll update it after server confirms, but without animation
    window.boardPreUpdated = false;
    
    // Submit the move (with promotion if needed)
    submitMove(promotionMove || move, boardFenBeforeMove);
    
    // Return nothing so piece stays where dropped
    // ChessBoard will keep it there until we update the position
    return;
}

function onSnapEnd() {
    // Don't update here - let submitMove handle board updates
    // This prevents double animations
}

async function submitMove(moveUCI, boardFenBeforeMove = null) {
    try {
        const response = await fetch('/api/training/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId,
                move: moveUCI
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Invalid move');
        }
        
        const data = await response.json();
        
        if (data.correct) {
            console.log('Move was correct! Response data:', data);
            
            // Update board position only if we haven't pre-updated it
            // This prevents double animation
            const wasPreUpdated = window.boardPreUpdated;
            window.boardPreUpdated = false; // Reset flag
            
            const ChessClass = getChessClass();
            if (!ChessClass) {
                console.error('Chess library not loaded');
                showError('Chess library not available');
                return;
            }
            try {
                currentGame = new ChessClass(data.boardFen);
                console.log('Game updated with FEN:', data.boardFen);
            } catch (error) {
                console.error('Error creating Chess instance:', error);
                showError('Failed to initialize chess game');
                return;
            }
            
            if (board) {
                // Disable CSS transitions temporarily to prevent animation glitch
                const boardElement = document.getElementById('chessboard');
                let originalTransitions = new Map();
                
                if (boardElement) {
                    // Store original transitions
                    originalTransitions.set(boardElement, boardElement.style.transition);
                    boardElement.style.transition = 'none';
                    
                    // Disable transitions on all piece images
                    const pieces = boardElement.querySelectorAll('img');
                    pieces.forEach(piece => {
                        originalTransitions.set(piece, piece.style.transition);
                        piece.style.transition = 'none';
                    });
                }
                
                // Update position (no animation due to disabled transitions)
                board.position(currentGame.fen());
                
                // Re-enable transitions after a tiny delay
                setTimeout(() => {
                    if (boardElement) {
                        boardElement.style.transition = originalTransitions.get(boardElement) || '';
                        const pieces = boardElement.querySelectorAll('img');
                        pieces.forEach(piece => {
                            piece.style.transition = originalTransitions.get(piece) || '';
                        });
                    }
                }, 10);
                
                console.log('Board position updated (animations disabled)');
            }
            
            // Clear hint
            clearHint();
            
            // Update position info - ensure proper structure
            if (data.positionInfo) {
                currentPosition = {
                    isUserTurn: data.positionInfo.isUserTurn !== false,
                    isComplete: data.positionInfo.isComplete || false,
                    correctMove: data.positionInfo.correctMove || null,
                    opponentMove: data.positionInfo.opponentMove || null,
                    userColor: data.userColor || currentPosition?.userColor || 'white'
                };
                console.log('Position info updated:', currentPosition);
            }
            
            updateStatus('Correct! ✅', 'success');
            
            // Handle opponent moves or line completion
            if (data.lineComplete) {
                updateStatus('Line Complete! 🎉', 'success');
                document.getElementById('next-line-btn').style.display = 'block';
            } else if (data.positionInfo && data.positionInfo.opponentMoveToPlay) {
                // Auto-play opponent move (backend already advanced, positionInfo is for after opponent move)
                console.log('Opponent move to play:', data.positionInfo.opponentMoveToPlay);
                setTimeout(() => {
                    playOpponentMove(data.positionInfo.opponentMoveToPlay, data.positionInfo);
                }, 500);
            } else if (data.positionInfo && data.positionInfo.isUserTurn) {
                // It's still user's turn - position already updated above
                console.log('Still user turn, waiting for next move');
                updateStatus('Correct! Make your next move', 'success');
            }
        } else {
            // Move was incorrect - revert board and snap piece back
            updateStatus('Incorrect ❌', 'error');
            
            // Revert board to state before the move
            if (boardFenBeforeMove && board) {
                const ChessClass = getChessClass();
                if (ChessClass) {
                    try {
                        currentGame = new ChessClass(boardFenBeforeMove);
                        board.position(boardFenBeforeMove);
                        console.log('Board reverted to previous position');
                    } catch (error) {
                        console.error('Error reverting board:', error);
                    }
                }
            }
            
            // Reset the pre-update flag
            window.boardPreUpdated = false;
            
            // Don't highlight correct move automatically - only when user clicks "Show Solution"
            // The correct move is stored in data.correctMove if needed later
            
            // Force snapback by triggering board update
            // The piece will snap back because board position was reverted
            if (board && pendingMove) {
                // Small delay to ensure snapback happens
                setTimeout(() => {
                    if (currentGame) {
                        board.position(currentGame.fen());
                    }
                }, 50);
            }
        }
        
        // Clear pending move
        pendingMove = null;
    } catch (error) {
        console.error('Error submitting move:', error);
        updateStatus('Error: ' + error.message, 'error');
        
        // On error, also revert board if we have the before state
        if (boardFenBeforeMove && board) {
            const ChessClass = getChessClass();
            if (ChessClass) {
                try {
                    currentGame = new ChessClass(boardFenBeforeMove);
                    board.position(boardFenBeforeMove);
                } catch (e) {
                    console.error('Error reverting board on error:', e);
                }
            }
        }
        
        // Clear pending move
        pendingMove = null;
        window.boardPreUpdated = false;
    }
}

async function playOpponentMove(moveUCI, nextPositionInfo) {
    console.log('Playing opponent move:', moveUCI);
    
    if (currentGame && board) {
        try {
            const fromSquare = moveUCI.substring(0, 2);
            const toSquare = moveUCI.substring(2, 4);
            const promotion = moveUCI.length > 4 ? moveUCI[4] : undefined;
            
            // Play the move in the game
            const move = currentGame.move({ from: fromSquare, to: toSquare, promotion: promotion });
            if (!move) return;
            
            // Simply update the board position - ChessBoard.js will handle the animation
            // The board is already in the correct state, so this should animate smoothly
            board.position(currentGame.fen());
            
            console.log('Opponent move played');
            
            // The backend already advanced past the opponent move, so nextPositionInfo
            // should be for the position AFTER opponent move (user's turn)
            if (nextPositionInfo) {
                currentPosition = {
                    isUserTurn: nextPositionInfo.isUserTurn !== false,
                    isComplete: nextPositionInfo.isComplete || false,
                    correctMove: nextPositionInfo.correctMove || null,
                    opponentMove: nextPositionInfo.opponentMove || null,
                    userColor: currentPosition?.userColor || 'white'
                };
                console.log('Position updated after opponent move:', currentPosition);
                
                // Update board with correct FEN if we have it
                if (nextPositionInfo.boardFen && board) {
                    const ChessClass = getChessClass();
                    if (ChessClass) {
                        currentGame = new ChessClass(nextPositionInfo.boardFen);
                        board.position(currentGame.fen());
                    }
                }
                
                if (currentPosition.isUserTurn) {
                    updateStatus('Your turn!', 'success');
                }
            } else {
                // Fallback - assume it's user's turn
                currentPosition = {
                    isUserTurn: true,
                    isComplete: false,
                    userColor: currentPosition?.userColor || 'white'
                };
                updateStatus('Your turn!', 'success');
            }
        } catch (error) {
            console.error('Error playing opponent move:', error);
            showError('Failed to play opponent move');
        }
    }
}

async function getCurrentPosition() {
    // This would be called after opponent move to get next position
    // For now, we'll reload the line to get updated position
    loadNextLine();
}

async function showHint() {
    try {
        const response = await fetch('/api/training/hint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get hint');
        }
        
        const data = await response.json();
        
        // Highlight the square
        clearHint();
        hintSquare = data.hintSquare;
        highlightSquare(hintSquare, 'hint');
        
        updateStatus('Hint: Starting square highlighted', 'info');
    } catch (error) {
        console.error('Error getting hint:', error);
        showError('Failed to get hint');
    }
}

async function showSolution() {
    try {
        // Just get the correct move without executing it
        // We can get it from the current position info if available
        let correctMove = null;
        
        if (currentPosition && currentPosition.correctMove) {
            // Use the correct move from current position
            correctMove = currentPosition.correctMove;
            console.log('Using correct move from current position:', correctMove);
        } else {
            // Fetch from backend - but we'll modify backend to just return the move without executing
            const response = await fetch('/api/training/solution', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: sessionId,
                    showOnly: true  // Flag to just show, not execute
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get solution');
            }
            
            const data = await response.json();
            correctMove = data.correctMove;
        }
        
        // Just highlight the move - don't execute it
        if (correctMove) {
            highlightMove(correctMove, 'correct');
            updateStatus('Solution: Correct move highlighted', 'info');
        } else {
            updateStatus('No solution available', 'error');
        }
        
        clearHint();
    } catch (error) {
        console.error('Error getting solution:', error);
        showError('Failed to get solution');
    }
}

async function loadNextLine() {
    try {
        updateStatus('Loading next line...', 'info');
        document.getElementById('next-line-btn').style.display = 'none';
        
        const response = await fetch('/api/training/next-line', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: sessionId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load line');
        }
        
        const data = await response.json();
        
        // Update UI
        document.getElementById('opening-name').textContent = data.openingName;
        document.getElementById('display-opening').textContent = data.openingName;
        
        // Initialize chess game - wait for Chess library if needed
        let ChessClass = getChessClass();
        if (!ChessClass) {
            // Wait a bit longer for async loading
            console.log('Chess library not found, waiting...');
            await new Promise(resolve => setTimeout(resolve, 500));
            ChessClass = getChessClass();
            
            if (!ChessClass) {
                console.error('Chess library still not loaded after waiting');
                console.log('Available window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('chess')));
                showError('Chess library failed to load. Please check your internet connection and refresh the page.');
                return;
            }
        }
        
        try {
            currentGame = new ChessClass(data.boardFen);
        } catch (error) {
            console.error('Error creating Chess instance:', error);
            showError('Failed to initialize chess game: ' + error.message);
            return;
        }
        
        // Wait for board to be ready
        if (board) {
            // Set orientation FIRST before setting position to avoid visual flip
            board.orientation(data.userColor);
            
            // Disable transitions during initial load to prevent pieces from loading unevenly
            const boardElement = document.getElementById('chessboard');
            if (boardElement) {
                const pieces = boardElement.querySelectorAll('img');
                pieces.forEach(piece => {
                    piece.style.transition = 'none';
                });
            }
            
            board.position(currentGame.fen());
            
            // Re-enable transitions after a brief moment
            setTimeout(() => {
                if (boardElement) {
                    const pieces = boardElement.querySelectorAll('img');
                    pieces.forEach(piece => {
                        piece.style.transition = '';
                    });
                }
            }, 100);
        } else {
            setTimeout(() => {
                if (board) {
                    // Set orientation FIRST before setting position to avoid visual flip
                    board.orientation(data.userColor);
                    
                    // Disable transitions during initial load
                    const boardElement = document.getElementById('chessboard');
                    if (boardElement) {
                        const pieces = boardElement.querySelectorAll('img');
                        pieces.forEach(piece => {
                            piece.style.transition = 'none';
                        });
                    }
                    
                    board.position(currentGame.fen());
                    
                    // Re-enable transitions after a brief moment
                    setTimeout(() => {
                        if (boardElement) {
                            const pieces = boardElement.querySelectorAll('img');
                            pieces.forEach(piece => {
                                piece.style.transition = '';
                            });
                        }
                    }, 100);
                }
            }, 200);
        }
        
        // Update position info - ensure isUserTurn defaults to true if not specified
        currentPosition = {
            isUserTurn: data.positionInfo?.isUserTurn !== false, // default to true
            isComplete: data.positionInfo?.isComplete || false,
            correctMove: data.positionInfo?.correctMove || null,
            opponentMove: data.positionInfo?.opponentMove || null,
            userColor: data.userColor || 'white'
        };
        
        console.log('Position info set:', currentPosition);
        
        // Handle opponent's first move if needed (for black openings)
        // Backend should have already handled this, but check just in case
        if (data.positionInfo && data.positionInfo.opponentMoveToPlay) {
            console.log('Initial opponent move to play:', data.positionInfo.opponentMoveToPlay);
            setTimeout(() => {
                playOpponentMove(data.positionInfo.opponentMoveToPlay, data.positionInfo);
            }, 300);
        }
        
        clearHint();
        updateStatus('Ready', 'success');
        
    } catch (error) {
        console.error('Error loading line:', error);
        showError(error.message);
    }
}

// UI Helper Functions
function updateStatus(message, type = 'info') {
    const statusText = document.getElementById('status-text');
    statusText.textContent = message;
    
    // Update status indicator color
    const indicator = statusText.parentElement;
    indicator.className = 'status-indicator';
    if (type === 'success') {
        indicator.style.background = '#d1fae5';
        indicator.style.color = '#10b981';
    } else if (type === 'error') {
        indicator.style.background = '#fee2e2';
        indicator.style.color = '#ef4444';
    } else {
        indicator.style.background = '#e0e7ff';
        indicator.style.color = '#6366f1';
    }
}

function highlightSquare(square, type) {
    const squareEl = document.querySelector(`[data-square="${square}"]`);
    if (squareEl) {
        squareEl.classList.add(type === 'hint' ? 'hint-square' : '');
    }
}

function highlightMove(moveUCI, type) {
    const from = moveUCI.substring(0, 2);
    const to = moveUCI.substring(2, 4);
    
    const fromEl = document.querySelector(`[data-square="${from}"]`);
    const toEl = document.querySelector(`[data-square="${to}"]`);
    
    if (fromEl) fromEl.classList.add(type === 'correct' ? 'correct-move' : 'incorrect-move');
    if (toEl) toEl.classList.add(type === 'correct' ? 'correct-move' : 'incorrect-move');
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
        if (fromEl) {
            fromEl.classList.remove('correct-move', 'incorrect-move');
        }
        if (toEl) {
            toEl.classList.remove('correct-move', 'incorrect-move');
        }
    }, 2000);
}

function clearHint() {
    if (hintSquare) {
        const squareEl = document.querySelector(`[data-square="${hintSquare}"]`);
        if (squareEl) {
            squareEl.classList.remove('hint-square');
        }
        hintSquare = null;
    }
}

function showError(message) {
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // Insert at top of current screen
    const activeScreen = document.querySelector('.screen.active');
    if (activeScreen) {
        activeScreen.insertBefore(errorDiv, activeScreen.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}



