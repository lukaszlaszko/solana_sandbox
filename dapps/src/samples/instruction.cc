#include "instruction.h"

#include <stdio.h>

Instruction::Instruction(const uint8_t* data, uint64_t data_len) : data_(*reinterpret_cast<const Data*>(data))
{
}

Instruction::Result Instruction::Invoke(SolAccountInfo* ka, uint64_t ka_num)
{
    switch (data_.code) {
        case NOOP: {
            sol_log("NOOP invoked!");
            break;
        }
        case MINT: {
            if (ka_num != 1ul) {
                sol_log("Number of accounts different than 1!");
                return ERROR_NOT_ENOUGH_ACCOUNT_KEYS;
            }

            const auto amount = data_.mint.amount;
            sol_log("Minting:");
            sol_log_64(0, 0, 0, sizeof(Data), amount);

            auto account = reinterpret_cast<Account*>(ka[0].data);
            return DoMint(*account, amount);
        }
    }

    return SUCCESS;
}

Instruction::Result Instruction::DoMint(Account& account, uint64_t amount)
{
    account.amount += amount;
    return SUCCESS;
}