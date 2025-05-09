/* Copyright (c) 2024 The Brave Authors. All rights reserved.
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at https://mozilla.org/MPL/2.0/. */

import * as React from 'react'
import ProgressRing from '@brave/leo/react/progressRing'

import { useLocaleContext } from '../../lib/locale_strings'
import { useAppState } from '../../lib/app_model_context'
import { useBreakpoint } from '../../lib/breakpoint'
import { BatUtilityCard } from './bat_utility_card'
import { CommunityCard } from './community_card'
import { MerchStoreCard } from './merch_store_card'
import { PartnerPromoCard } from './partner_promo_card'

import { style } from './explore_view.style'

export function ExploreView() {
  const { getString } = useLocaleContext()
  const viewType = useBreakpoint()
  const cards = useAppState((state) => state.cards)

  if (!cards) {
    return (
      <div data-css-scope={style.scope}>
        <div className='loading'>
          <ProgressRing />
        </div>
      </div>
    )
  }

  if (viewType === 'double') {
    return (
      <div data-css-scope={style.scope}>
        <h3>{getString('navigationExploreLabel')}</h3>
        <div className='columns'>
          <div>
            <PartnerPromoCard />
            <MerchStoreCard />
          </div>
          <div>
            <BatUtilityCard />
            <CommunityCard />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-css-scope={style.scope}>
      <h3>{getString('navigationExploreLabel')}</h3>
      <PartnerPromoCard />
      <MerchStoreCard />
      <BatUtilityCard />
      <CommunityCard />
    </div>
  )
}
