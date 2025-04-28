import express from 'express';
import { Request, Response } from 'express';
import { Pool } from 'pg';
import { generatePasswordHash, checkPasswordHash } from 'node-password-hash';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';

const app = express();
const port = process.env.PORT || 5000;

// -----------------------------------Database---------------------------------------
// Configuration - PostgreSQL
const pool = new Pool({
    host: 'your_database_host',
    port: 5432,
    database: 'your_database_name',
    user: 'your_database_user',
    password: 'your_database_password',
});

// Database connection check
const connectToDatabase = async () => {
    try {
        const client = await pool.connect();
        console.log('Connected to PostgreSQL database');
        client.release();
    } catch (error) {
        console.error('Error connecting to database:', error);
        //  Don't throw here, let the app start and handle DB connection later
    }
};
connectToDatabase();
// -----------------------------------End Database---------------------------------------


// -----------------------------------Backend---------------------------------------
// Helper function to get user role
const getUserRole = async (userId: string): Promise<string | null> => {
    const client = await pool.connect();
    try {
        const result = await client.query('SELECT role FROM users WHERE id = $1', [userId]);
        if (result.rows.length > 0) {
            return result.rows[0].role;
        }
        return null;
    } catch (error) {
        console.error("Error in getUserRole:", error);
        throw error; // Re-throw to be caught by the route handler
    } finally {
        client.release();
    }
};

// Authentication middleware
const tokenRequired = async (req: Request, res: Response, next: () => void) => {
    const token = req.headers.authorization;
    if (!token) {
        return res.status(401).json({ error: 'Token is missing' });
    }

    try {
        // In a real app, you'd verify the token (e.g., JWT)
        // For simplicity, we'll just check if it's a non-empty string
        if (typeof token !== 'string' || token.length === 0) {
            throw new Error("Invalid Token");
        }
        //  In a real application, you would decode the token
        //  and get the user ID from it.  This is a placeholder.
        const userId = 'mock_user_id'; // Replace with actual user ID from token
        req.userId = userId; // Store user ID in request
        next();
    } catch (error: any) {
        return res.status(401).json({ error: 'Invalid token', message: error.message });
    }
};

// Admin-only middleware
const adminRequired = async (req: Request, res: Response, next: () => void) => {
    try {
        const role = await getUserRole(req.userId!); // Use the userId from the tokenRequired middleware
        if (role !== 'admin') {
            return res.status(403).json({ error: 'Admin access required' });
        }
        next();
    } catch (error) {
        // Handle errors from getUserRole
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
};

// Routes

// Serve the main HTML page
app.get('/', (req: Request, res: Response) => {
    res.sendFile(path.join(__dirname, 'frontend/build/index.html'));
});

// Register a new user
app.post('/register', async (req: Request, res: Response) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password are required' });
    }

    try {
        const client = await pool.connect();
        try {
            // Check if the email is already taken
            const emailCheckResult = await client.query('SELECT id FROM users WHERE email = $1', [email]);
            if (emailCheckResult.rows.length > 0) {
                return res.status(400).json({ error: 'Email already taken' });
            }

            // Hash the password
            const hashedPassword = generatePasswordHash(password);
            const userId = uuidv4();
            await client.query(
                'INSERT INTO users (id, email, password, role) VALUES ($1, $2, $3, $4)',
                [userId, email, hashedPassword, 'customer']
            );
            res.status(201).json({ message: 'User registered successfully' });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /register:", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Login a user and return a token
app.post('/login', async (req: Request, res: Response) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password are required' });
    }

    try {
        const client = await pool.connect();
        try {
            const result = await client.query('SELECT id, email, password FROM users WHERE email = $1', [email]);
            if (result.rows.length === 0) {
                return res.status(401).json({ error: 'Invalid credentials' });
            }

            const user = result.rows[0];
            if (!checkPasswordHash(password, user.password)) {
                return res.status(401).json({ error: 'Invalid credentials' });
            }

            // In a real app, use JWT (or similar) to create a secure token.
            const token = uuidv4(); // Mock token
            res.status(200).json({ token, username: user.email });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /login:", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Get user dashboard
app.get('/dashboard', tokenRequired, async (req: Request, res: Response) => {
    try {
        const client = await pool.connect();
        try {
            const userId = req.userId!;
            // Get the user's primary account.
            const accountResult = await client.query(
                'SELECT id, account_number, balance FROM accounts WHERE user_id = $1',
                [userId]
            );
            if (accountResult.rows.length === 0) {
                return res.status(404).json({ error: 'No account found for this user' });
            }

            const account = accountResult.rows[0];
            const accountId = account.id;
            const accountNumber = account.account_number;
            const balance = account.balance;

            // Get the last 10 transactions for the account.
            const transactionResult = await client.query(
                'SELECT id, type, amount, date, description FROM transactions WHERE account_id = $1 ORDER BY date DESC LIMIT 10',
                [accountId]
            );
            const transactions = transactionResult.rows.map(t => ({
                id: t.id,
                type: t.type,
                amount: t.amount,
                date: t.date,
                description: t.description,
            }));

            res.status(200).json({ accountNumber, accountBalance: balance, transactions });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /dashboard:", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Transfer funds
app.post('/transfer', tokenRequired, async (req: Request, res: Response) => {
    const { fromAccountNumber, toAccountNumber, amount } = req.body;

    if (!fromAccountNumber || !toAccountNumber || !amount) {
        return res.status(400).json({ error: 'From account, to account, and amount are required' });
    }

    if (amount <= 0) {
        return res.status(400).json({ error: 'Amount must be greater than zero' });
    }

    const client = await pool.connect();
    try {
        await client.query('BEGIN'); // Start transaction
        try {
            // 1. Get the sender's account and user ID
            const fromAccountResult = await client.query(
                'SELECT id, user_id, balance FROM accounts WHERE account_number = $1',
                [fromAccountNumber]
            );
            if (fromAccountResult.rows.length === 0) {
                await client.query('ROLLBACK');
                return res.status(404).json({ error: 'Sender account not found' });
            }

            const fromAccount = fromAccountResult.rows[0];
            const fromAccountId = fromAccount.id;
            const fromUserId = fromAccount.user_id;
            const fromBalance = fromAccount.balance;

            // 2. Verify that the user making the request owns the sender account
            if (req.userId !== fromUserId) {
                await client.query('ROLLBACK');
                return res.status(403).json({ error: 'Unauthorized to transfer from this account' });
            }

            // 3. Get the recipient's account.
            const toAccountResult = await client.query(
                'SELECT id, balance FROM accounts WHERE account_number = $1',
                [toAccountNumber]
            );
            if (toAccountResult.rows.length === 0) {
                await client.query('ROLLBACK');
                return res.status(404).json({ error: 'Recipient account not found' });
            }
            const toAccountId = toAccountResult.rows[0].id;
            const toBalance = toAccountResult.rows[0].balance;

            // 4. Check for sufficient funds.
            if (fromBalance < amount) {
                await client.query('ROLLBACK');
                return res.status(400).json({ error: 'Insufficient funds' });
            }

            // 5. Perform the transfer within a transaction (all-or-nothing).
            // 6. Debit the amount from the sender's account.
            await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromAccountId]);

            // 7. Credit the amount to the recipient's account.
            await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toAccountId]);

            // 8. Record the transaction for the sender.
            const transactionId = uuidv4();
            await client.query(
                'INSERT INTO transactions (id, account_id, type, amount, description) VALUES ($1, $2, $3, $4, $5)',
                [transactionId, fromAccountId, 'debit', amount, `Transfer to ${toAccountNumber}`]
            );

            // 9. Record the transaction for the recipient.
            const transactionIdTo = uuidv4();
            await client.query(
                'INSERT INTO transactions (id, account_id, type, amount, description) VALUES ($1, $2, $3, $4, $5)',
                [transactionIdTo, toAccountId, 'credit', amount, `Transfer from ${fromAccountNumber}`]
            );

            await client.query('COMMIT');
            res.status(200).json({ message: 'Transfer successful', transactionId });
        } catch (error: any) {
            await client.query('ROLLBACK');
            console.error("Error in /transfer:", error);
            return res.status(500).json({ error: 'Transaction failed', message: error.message });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /transfer (outer):", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Submit a complaint
app.post('/complaints', tokenRequired, async (req: Request, res: Response) => {
    const { details } = req.body;

    if (!details) {
        return res.status(400).json({ error: 'Complaint details are required' });
    }

    try {
        const client = await pool.connect();
        try {
            const userId = req.userId!;
            const complaintId = uuidv4();
            await client.query(
                'INSERT INTO complaints (id, user_id, details, status) VALUES ($1, $2, $3, $4)',
                [complaintId, userId, details, 'submitted']
            );
            res.status(201).json({ message: 'Complaint submitted successfully', complaintId });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /complaints (POST):", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Get complaint status
app.get('/complaints/:complaintId', tokenRequired, async (req: Request, res: Response) => {
    const { complaintId } = req.params;
    try {
        const client = await pool.connect();
        try {
            const userId = req.userId!;
            const result = await client.query(
                'SELECT user_id, status FROM complaints WHERE id = $1',
                [complaintId]
            );

            if (result.rows.length === 0) {
                return res.status(404).json({ error: 'Complaint not found' });
            }

            const complaint = result.rows[0];
            if (complaint.user_id !== userId) {
                return res.status(403).json({ error: 'Unauthorized to access this complaint' });
            }

            res.status(200).json({ complaintId, status: complaint.status });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /complaints/:complaintId (GET):", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// Get all users (admin only)
app.get('/admin/users', tokenRequired, adminRequired, async (req: Request, res: Response) => {
    try {
        const client = await pool.connect();
        try {
            const result = await client.query('SELECT id, email, role FROM users');
            const users = result.rows.map(user => ({
                id: user.id,
                email: user.email,
                role: user.role,
            }));
            res.status(200).json({ users });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error("Error in /admin/users:", error);
        return res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});
// -----------------------------------End Backend---------------------------------------


// -----------------------------------Frontend---------------------------------------
// Catch-all route to serve the React app's index.html for any unknown routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/build/index.html'));
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
// -----------------------------------End Frontend---------------------------------------
