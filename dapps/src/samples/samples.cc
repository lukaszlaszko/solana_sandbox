#include "instruction.h"

#include <solana_sdk.h>
#include <stdlib.h>

extern uint64_t entrypoint(const uint8_t* input)
{
    SolAccountInfo ka[1];
    SolParameters params = (SolParameters){.ka = ka};

    if (!sol_deserialize(input, &params, SOL_ARRAY_SIZE(ka))) {
        return ERROR_INVALID_ARGUMENT;
    }

    Instruction instruction{params.data, params.data_len};
    return instruction.Invoke(params.ka, params.ka_num);
}