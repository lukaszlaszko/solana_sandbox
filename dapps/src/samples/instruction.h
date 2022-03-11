#pragma once

#include "account.h"

#include <solana_sdk.h>

class Instruction final
{
public:
    using Result = uint64_t;

    /**
     * @brief Reconstructs instruction from the given buffer.
     */
    Instruction(const uint8_t* data, uint64_t data_len);

    /**
     * @brief Execute instruction on given parameters.
     */
    Result Invoke(SolAccountInfo* ka, uint64_t ka_num);

private:
    enum Code : uint8_t {
        NOOP = 0,
        MINT = 1,
//        DEPOSIT = 2,
//        WITHDRAW = 3
    };

    struct MintData
    {
        uint64_t amount;
    };

    struct Data
    {
        Code code;
        union {
            MintData mint;
        };
    };

    Result DoMint(Account& account, uint64_t amount);

    const Data& data_;
};