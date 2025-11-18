import { Body1, Divider, Text } from '@fluentui/react-components';
import { InfoRegular } from '@fluentui/react-icons';

import styles from './UsageInfo.module.css';

interface ITokenUsageInfo {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

interface IUsageInfoProps {
  info: ITokenUsageInfo;
  duration?: number;
}

export function UsageInfo({ info, duration }: IUsageInfoProps): React.ReactElement {
  return (
    <div className={styles.usageInfoContainer}>
      <div className={styles.usageSummary}>
        {duration !== undefined && (
          <>
            <span>{`${duration.toFixed(0)}ms`}</span>
            <span className={styles.divider}>|</span>
          </>
        )}
        <span>{`${info.total_tokens} tokens`}</span>
        <button 
          className={styles.infoButton}
          title="Usage information"
        >
          <InfoRegular className={styles.infoIcon} />
        </button>
      </div>
      <div className={styles.usageDetails}>
        <Text weight="semibold" size={200}>Usage Information</Text>
        <Divider className={styles.detailsDivider} />
        <div className={styles.detailsList}>
          <div className={styles.detailsItem}>
            <Body1 className={styles.detailLabel}>Input</Body1>
            <Body1 className={styles.detailValue}>{info.prompt_tokens}</Body1>
          </div>
          <div className={styles.detailsItem}>
            <Body1 className={styles.detailLabel}>Output</Body1>
            <Body1 className={styles.detailValue}>{info.completion_tokens}</Body1>
          </div>
        </div>
      </div>
    </div>
  );
}