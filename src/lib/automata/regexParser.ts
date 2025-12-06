export type NodeType = 'Union' | 'Concat' | 'Star' | 'Literal' | 'Epsilon';

export interface ASTNode {
    type: NodeType;
    value?: string;
    left?: ASTNode;
    right?: ASTNode;
}

export class RegexParser {
    private pos: number = 0;
    private input: string;

    constructor(input: string) {
        this.input = input.replace(/\s+/g, ''); // Remove whitespace
    }

    public parse(): ASTNode {
        this.pos = 0;
        const result = this.parseExpression();
        if (this.pos < this.input.length) {
            throw new Error(`Unexpected character at index ${this.pos}: ${this.input[this.pos]}`);
        }
        return result;
    }

    // Expression -> Term { '|' Term } or { '+' Term }
    private parseExpression(): ASTNode {
        let left = this.parseTerm();

        while (this.match('|') || this.match('+')) {
            const right = this.parseTerm();
            left = { type: 'Union', left, right };
        }

        return left;
    }

    // Term -> Factor { Factor }  (Implicit Concatenation)
    private parseTerm(): ASTNode {
        let left = this.parseFactor();

        // While we have a valid start of a Factor, treat it as concatenation
        // Stop at Union operators ('|', '+') or closing parenthesis
        while (this.pos < this.input.length && !['|', '+', ')'].includes(this.input[this.pos])) {
            const right = this.parseFactor();
            left = { type: 'Concat', left, right };
        }

        return left;
    }

    // Factor -> Base { '*' }
    private parseFactor(): ASTNode {
        let node = this.parseBase();

        while (this.match('*')) {
            node = { type: 'Star', left: node };
        }

        return node;
    }

    // Base -> Char | '(' Expression ')' | Epsilon
    private parseBase(): ASTNode {
        if (this.match('(')) {
            const node = this.parseExpression();
            if (!this.match(')')) {
                throw new Error("Expected ')'");
            }
            return node;
        }

        if (this.pos < this.input.length) {
            const char = this.input[this.pos];
            // Disallow special characters from being literals
            if (['|', '+', '*', ')'].includes(char)) {
                throw new Error(`Unexpected character: ${char}`);
            }
            this.pos++;
            // Treat 'ε' as Epsilon node
            if (char === 'ε') {
                return { type: 'Epsilon', value: 'ε' };
            }
            return { type: 'Literal', value: char };
        }

        throw new Error("Unexpected end of input");
    }

    private match(char: string): boolean {
        if (this.pos < this.input.length && this.input[this.pos] === char) {
            this.pos++;
            return true;
        }
        return false;
    }
}
